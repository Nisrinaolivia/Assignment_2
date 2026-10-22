"""Main tool page: the user describes an incident and the app runs the assessment pipeline."""

from io import BytesIO
from pathlib import Path

import streamlit as st

from utils.credentials import credentials_sidebar
from utils.export import build_memo_docx, build_statement_docx
from utils.llm import MODELS, SHARED_MODELS, get_client
from utils.pipeline import STEPS, run_assessment

st.set_page_config(page_title="Breach Assessment", page_icon="🔍", layout="wide")
credentials_sidebar()

TEST_DIR = Path(__file__).resolve().parent.parent / "test_files"
SAMPLES = {
    "— write my own —": None,
    "Test case 1: Hacked dental patient database": "scenario_1.txt",
    "Test case 2: Lost encrypted laptop, remotely wiped": "scenario_2.txt",
    "Test case 3: Misdirected tax return (small accounting firm)": "scenario_3.txt",
}
CONCLUSION_STYLE = {
    "eligible data breach": ("error", "🚨", "Notification to the OAIC and affected individuals is required."),
    "not an eligible data breach": ("success", "✅", "No notification is required under the NDB scheme."),
    "not covered by the NDB scheme": ("info", "ℹ️", "The NDB scheme does not apply to this entity or information."),
    "uncertain - more facts needed": ("warning", "⚠️", "Complete an assessment within 30 days (s 26WH)."),
}


def read_upload(file):
    """Extracts text from an uploaded .txt, .docx or .pdf incident report."""
    name = file.name.lower()
    data = file.getvalue()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    if name.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(BytesIO(data)).paragraphs)
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
    return ""


def badge(step, res):
    if step == "entity":
        return {"yes": "✅ Covered", "partly": "◐ Partly covered", "no": "❌ Not covered"}.get(
            res.get("covered"), "❓ Uncertain")
    if step == "remedial":
        return "⚠️ Exception applies" if res.get("satisfied") else "Exception does not apply"
    return "✅ Satisfied" if res.get("satisfied") else "❌ Not satisfied"


def show_sources(passages, method):
    with st.popover(f"📚 OAIC sources ({len(passages)})"):
        st.caption(f"Retrieved by {method} from Part 4 of the OAIC guide.")
        for p in passages:
            heading = p["section"] + (f" — {p['subsection']}" if p["subsection"] else "")
            st.markdown(f"**[OAIC p {p['page']}]** {heading}")
            st.caption(p["text"][:600] + ("…" if len(p["text"]) > 600 else ""))


# ---------------------------------------------------------------- input
st.title("🔍 Breach Assessment")
st.caption("Describe a data incident. The tool works through Part IIIC of the Privacy Act 1988 (Cth) "
           "step by step, grounded in the statute and the OAIC's guidance.")

left, right = st.columns([3, 2], gap="large")
with left:
    choice = st.selectbox("Load a test case (optional)", list(SAMPLES))
    default_text = (TEST_DIR / SAMPLES[choice]).read_text() if SAMPLES[choice] else ""
    upload = st.file_uploader("…or upload an incident report", type=["txt", "docx", "pdf"])
    if upload is not None:
        default_text = read_upload(upload) or default_text
    incident = st.text_area(
        "Incident description",
        value=default_text,
        height=240,
        key=f"incident_{choice}_{upload.name if upload else ''}",
        placeholder="Who holds the data, what happened, what information was involved, who may have it, "
                    "what security measures applied, and what has been done since.",
    )
with right:
    st.markdown("**Tips for a better assessment**")
    st.markdown(
        "- Say who the entity is and roughly its **annual turnover** or sector\n"
        "- List the **kinds of information** involved\n"
        "- Mention **encryption** or other security measures\n"
        "- Describe **who** may have the data and **what you have done** since"
    )
    with st.expander("Settings"):
        shared = st.session_state.get("using_shared_key")
        model = st.selectbox(
            "AI model",
            SHARED_MODELS if shared else MODELS,
            help="The 'mini' models are faster and cheaper; gpt-4o and gpt-4.1 are more capable "
                 "but slower and more expensive. Password users can choose the mini models only.",
        )
        show_json = st.checkbox("Show raw AI output")

if st.button("Assess", type="primary", disabled=not incident.strip()):
    client = get_client()
    st.session_state["ai_calls"] = 0
    with st.status("Running assessment...", expanded=True) as status:
        try:
            result = run_assessment(client, incident, model, progress=st.write)
        except Exception as err:  # e.g. invalid key, model not available, rate limit
            status.update(label="The assessment could not be completed", state="error")
            st.error(f"OpenAI returned an error: {err}\n\nCheck your API key, or try another model "
                     "under Settings.")
            st.stop()
        result["ai_calls"] = st.session_state["ai_calls"]
        status.update(label=f"Done: {result['ai_calls']} AI calls made", state="complete", expanded=False)
    st.session_state["result"] = result

# ---------------------------------------------------------------- output
result = st.session_state.get("result")
if not result:
    st.stop()

st.divider()
final = result["conclusion"]
kind, icon, note = CONCLUSION_STYLE.get(final, ("warning", "⚠️", ""))
getattr(st, kind)(f"### {icon} {final.upper()}\n{note}")

results = result["results"]
all_passages = [p for r in results.values() for p in r["_passages"]] + result.get("statement_passages", [])
m1, m2, m3, m4 = st.columns(4)
m1.metric("AI calls", result["ai_calls"])
m2.metric("Review rounds", len(result["reviews"]))
m3.metric("Steps revised", len(result["revisions"]))
m4.metric("OAIC passages used", len({(p["page"], p["id"]) for p in all_passages}))

if result["rule_based"] != final:
    st.info(f"**Rule-based logic** gave *{result['rule_based']}*, but the senior reviewer concluded "
            f"*{final}*. See the Review tab for why.")

unknowns = [u for u in result["facts"].get("unknowns", []) if u]
if unknowns:
    with st.expander(f"❓ {len(unknowns)} missing fact(s) that could change the outcome"):
        for u in unknowns:
            st.markdown(f"- {u}")
        st.caption("Add these facts to the description and run the assessment again.")

tabs = st.tabs(["⚖️ Analysis", "📊 Serious harm factors", "🔁 Review loop", "📝 Advice memo",
                "📨 OAIC statement", "🗂️ Facts"])

with tabs[0]:
    for step, res in results.items():
        with st.container(border=True):
            st.markdown(f"**{STEPS[step][0]}** — {badge(step, res)} · *{res.get('confidence', '?')} confidence*")
            if step == "entity" and res.get("basis"):
                st.caption(f"Basis: {res['basis']}" + (f" · Scope: {res['scope_note']}" if res.get("scope_note") else ""))
            st.write(res.get("reasoning", ""))
            show_sources(res["_passages"], res["_retrieval"])
            if show_json:
                st.json({k: v for k, v in res.items() if not k.startswith("_")})

with tabs[1]:
    e2 = results["element_2"]
    factors = e2.get("factors") or []
    if factors:
        icons = {"increases risk": "🔺", "reduces risk": "🔻", "neutral": "▫️", "unknown": "❔"}
        st.table([{"s 26WG matter": f.get("factor", ""), "Finding": f.get("finding", ""),
                   "Effect": f"{icons.get(f.get('effect'), '')} {f.get('effect', '')}"} for f in factors])
    if e2.get("likely_harms"):
        st.markdown("**Kinds of harm considered:** " + ", ".join(e2["likely_harms"]))
    st.markdown(f"**Overall:** {badge('element_2', e2)} — {e2.get('reasoning', '')}")

with tabs[2]:
    for review in result["reviews"]:
        with st.container(border=True):
            st.markdown(f"**Round {review['_round']}** · rule-based result: *{review['_rule_based']}* · "
                        f"reviewer: *{review.get('revised_conclusion', '?')}*")
            for issue in review.get("issues_found") or []:
                st.markdown(f"- {issue}")
            if not review.get("issues_found"):
                st.caption("No issues found.")
            st.write(review.get("explanation", ""))
            for rev in [r for r in result["revisions"] if r["round"] == review["_round"]]:
                st.markdown(f"↪️ **Sent back:** {rev['label']}  \n*Feedback:* {rev['feedback']}  \n"
                            f"*Before:* `{rev['before']}` → *After:* `{rev['after']}`")

with tabs[3]:
    st.markdown(result["memo"])

    def label(step, res):
        text = badge(step, res)
        first, _, rest = text.partition(" ")
        return rest if rest and not first.isalpha() else text  # drop the leading emoji only

    memo_docx = build_memo_docx(
        result["memo"], final,
        [(STEPS[s][0], label(s, r), r.get("reasoning")) for s, r in results.items()]
        + [("Senior review", final, (result["reviews"][-1].get("issues_found") or [])
            + [result["reviews"][-1].get("explanation", "")])],
        factors=factors,
        sources=all_passages,
    )
    st.download_button("⬇️ Download memo (.docx)", memo_docx, file_name="ndb_assessment_memo.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

with tabs[4]:
    if result.get("statement"):
        st.caption("Draft statement under s 26WK. Complete every [to be confirmed] item before lodging.")
        st.markdown(result["statement"])
        st.download_button(
            "⬇️ Download draft statement (.docx)",
            build_statement_docx(result["statement"], result["facts"].get("entity")),
            file_name="s26WK_statement_draft.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    else:
        st.info("A statement to the Commissioner is only drafted when the conclusion is an eligible data breach.")

with tabs[5]:
    st.json(result["facts"])
