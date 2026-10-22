"""Main tool page: user describes an incident and the app runs 6 AI calls."""

import json
from pathlib import Path

import streamlit as st

from utils.credentials import credentials_sidebar
from utils.llm import get_client, ask
from utils import prompts as P
from utils.export import build_memo_docx
from knowledge import ndb_law as L

st.set_page_config(page_title="Breach Assessment", page_icon="🔍", layout="centered")
credentials_sidebar()

st.title("🔍 Breach Assessment")

TEST_DIR = Path(__file__).resolve().parent.parent / "test_files"

SAMPLES = {
    "— write my own —": "",
    "Sample 1: Hacked customer database": (TEST_DIR / "scenario_1.txt").read_text(),
    "Sample 2: Lost encrypted laptop": (TEST_DIR / "scenario_2.txt").read_text(),
    "Sample 3: Misdirected email (borderline)": (TEST_DIR / "scenario_3.txt").read_text(),
}

choice = st.selectbox("Start from a sample scenario (optional)", list(SAMPLES))
incident = st.text_area(
    "Describe the incident",
    value=SAMPLES[choice],
    height=220,
    placeholder="What happened, what information was involved, who may have seen it, what you've done since...",
)
show_json = st.checkbox("Show raw AI output for each step")

if st.button("Assess", type="primary", disabled=not incident.strip()):
    client = get_client()
    st.session_state["ai_calls"] = 0

    def element(task, law, facts):
        return ask(client, P.ELEMENT_TEMPLATE.format(law=law, task=task),
                   json.dumps(facts), as_json=True)

    def badge(ok):
        return "✅ Satisfied" if ok else "❌ Not satisfied"

    with st.status("Running assessment...", expanded=True) as status:
        # Step 1
        st.write("Step 1: extracting facts")
        facts = ask(client, P.EXTRACT_FACTS, incident, as_json=True)

        # Step 2
        st.write("Step 2: unauthorised access, disclosure or loss")
        e1 = element(P.ELEMENT_1_TASK, L.ELEMENT_1_LAW, facts)

        # Step 3
        st.write("Step 3: likely serious harm")
        e2 = element(P.ELEMENT_2_TASK, L.ELEMENT_2_LAW, facts)

        # Step 4
        st.write("Step 4: remedial action exception")
        e3 = element(P.ELEMENT_3_TASK, L.ELEMENT_3_LAW, facts)

        # If-then logic (Lab 1 style)
        preliminary = bool(e1["satisfied"] and e2["satisfied"] and not e3["satisfied"])

        # Step 5
        st.write("Step 5: reflection")
        review = ask(client, P.REFLECTION, json.dumps({
            "facts": facts, "element_1": e1, "element_2": e2, "remedial_exception": e3,
            "preliminary_conclusion": "eligible data breach" if preliminary else "not an eligible data breach",
        }), as_json=True)

        # Step 6
        st.write("Step 6: drafting memo")
        memo = ask(client, P.MEMO, json.dumps({
            "facts": facts, "element_1": e1, "element_2": e2,
            "remedial_exception": e3, "review": review,
        }))
        status.update(label=f"Done: {st.session_state['ai_calls']} AI calls made",
                      state="complete", expanded=False)

    # ---------- Output ----------
    final = review.get("revised_conclusion", "")
    if final == "eligible data breach":
        st.error(f"**Conclusion: {final.upper()}**: notification likely required.")
    elif final == "not an eligible data breach":
        st.success(f"**Conclusion: {final.upper()}**")
    else:
        st.warning(f"**Conclusion: {final.upper()}**")

    for title, res, label in [
        ("Element 1: Unauthorised access / disclosure / loss", e1, badge(e1["satisfied"])),
        ("Element 2: Likely serious harm", e2, badge(e2["satisfied"])),
        ("Exception: Remedial action (s 26WF)", e3,
         "⚠️ Exception applies" if e3["satisfied"] else "Exception does not apply"),
    ]:
        with st.expander(f"{title}: {label} ({res.get('confidence', '?')} confidence)"):
            st.write(res["reasoning"])
            if show_json:
                st.json(res)

    with st.expander("Reflection (self-review)"):
        if review.get("issues_found"):
            for i in review["issues_found"]:
                st.markdown(f"- {i}")
        else:
            st.write("No issues found.")
        st.write(review.get("explanation", ""))

    if show_json:
        with st.expander("Extracted facts"):
            st.json(facts)

    st.subheader("Advice memo")
    st.markdown(memo)

    # ---------- Word download ----------
    def label(res, is_exception=False):
        if is_exception:
            return "Exception applies" if res.get("satisfied") else "Exception does not apply"
        return "Satisfied" if res.get("satisfied") else "Not satisfied"

    docx_bytes = build_memo_docx(
        memo,
        final,
        [
            ("Element 1: Unauthorised access, disclosure or loss", label(e1), e1.get("reasoning")),
            ("Element 2: Likely serious harm", label(e2), e2.get("reasoning")),
            ("Exception: Remedial action (s 26WF)", label(e3, True), e3.get("reasoning")),
            ("Reflection (self-review)", final, (review.get("issues_found") or []) + [review.get("explanation", "")]),
        ],
    )
    st.download_button(
        "⬇️ Download memo (.docx)",
        data=docx_bytes,
        file_name="ndb_assessment_memo.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        on_click="ignore",  # keep the results on screen after downloading
    )
