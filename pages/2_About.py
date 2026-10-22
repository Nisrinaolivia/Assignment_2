import streamlit as st
from utils.credentials import credentials_sidebar

st.set_page_config(page_title="About", page_icon="ℹ️")
credentials_sidebar()

st.title("ℹ️ About this tool")
st.markdown(
    """
- **Subject:** LAWS90286 Legal AI: Design and Development, Assignment 2
- **Author:** Denise

### Design
The legal test for an *eligible data breach* (Privacy Act 1988 (Cth) s 26WE) is broken
into discrete steps, each handled by a separate AI call grounded in the text of the
relevant provisions. Boolean logic combines the results, and a reflection step reviews
the whole analysis before a memo is drafted. Each run makes **6 AI calls**.

### Known limitations
- Only as good as the facts given; missing facts are flagged but not investigated.
- "Serious harm" is evaluative; the AI may be inconsistent on borderline facts.
- Does not check whether the entity is an APP entity or credit reporting body,
  and does not cover the Tax File Number rules or the My Health Records Act scheme.
- Only the core provisions (ss 6, 26WE, 26WF, 26WG) are given to the AI; OAIC guidance
  and case examples are not yet included.
"""
)