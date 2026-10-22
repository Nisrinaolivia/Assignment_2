"""
Home.py — main page / landing page of the app.
Run locally with:  streamlit run Home.py
On Streamlit Cloud, set "Main file path" to Home.py.
"""

import streamlit as st
from utils.credentials import credentials_sidebar

st.set_page_config(
    page_title="NDB Checker",
    page_icon="⚖️",
    layout="centered",
)

# API key / password sidebar (shown on every page)
credentials_sidebar()

# ---------- Header ----------
st.title("⚖️ Notifiable Data Breach Checker")
st.caption("An AI-assisted tool for assessing breaches under Part IIIC of the Privacy Act 1988 (Cth)")

st.markdown(
    """
When personal information is compromised, an organisation covered by the
*Privacy Act 1988* (Cth) must decide whether the incident is an
**eligible data breach** that has to be notified to the OAIC and affected individuals.

This tool takes a plain-English description of an incident and works through
that question step by step. Each legal step is grounded in the text of the Act and in passages
retrieved from the OAIC's *Data breach preparation and response* guide, which the tool cites.
"""
)

st.divider()

# ---------- How it works ----------
st.subheader("How it works")

steps = [
    ("1. Fact extraction", "Turns your description (typed or uploaded) into structured facts and flags missing ones."),
    ("2. Coverage", "Is the entity covered? APP entities, small business exceptions, TFN rules, employee records."),
    ("3. Element 1", "Unauthorised access, disclosure or loss of personal information (s 26WE(2))."),
    ("4. Element 2", "Likely serious harm, assessed factor by factor under s 26WG."),
    ("5. Remedial action", "Does the s 26WF exception apply?"),
    ("6. Senior review loop", "A reviewer checks the analysis and sends flawed steps back for revision."),
    ("7. Advice memo", "A memo with citations, downloadable as a Word document."),
    ("8. OAIC statement", "If notifiable, a draft s 26WK statement to the Commissioner."),
]

cols = st.columns(2)
for i, (title, desc) in enumerate(steps):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(desc)

st.divider()

# ---------- Getting started ----------
st.subheader("Getting started")
st.markdown(
    """
1. Enter your **OpenAI API key** in the sidebar (or the access password, if you have one).
2. Open **Breach Assessment** from the sidebar menu.
3. Describe the incident (or load one of the sample scenarios) and click **Assess**.
"""
)

if st.session_state.get("openai_api_key"):
    st.success("Access ready. You're good to go.")
    st.page_link("pages/1_Breach_Assessment.py", label="Go to Breach Assessment →", icon="🔍")
else:
    st.info("Enter your OpenAI API key or the access password in the sidebar to begin.")

st.divider()

# ---------- Disclaimer ----------
st.warning(
    "**Not legal advice.** This tool is a student project (LAWS90286, Melbourne Law School). "
    "Its output may be wrong and must be reviewed by a qualified practitioner.",
    icon="⚠️",
)
