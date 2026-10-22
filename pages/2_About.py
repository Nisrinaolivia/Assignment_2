import streamlit as st
from utils.credentials import credentials_sidebar

st.set_page_config(page_title="About", page_icon="ℹ️")
credentials_sidebar()

st.title("ℹ️ About this tool")
st.markdown(
    """
- **Subject:** LAWS90286 Legal AI: Design and Development, Assignment 2
- **Author:** Denise

### Legal design
Whether an incident must be notified under Part IIIC of the *Privacy Act 1988* (Cth) is broken
into the questions a privacy lawyer would ask, in order:

1. **Coverage**: is the entity (and this kind of information) subject to the NDB scheme?
2. **Element 1**: unauthorised access, unauthorised disclosure, or loss (s 26WE(2)).
3. **Element 2**: would a reasonable person conclude serious harm is *likely*? Each s 26WG
   matter is assessed separately.
4. **Exception**: did remedial action prevent likely serious harm (s 26WF)?

The results are combined with boolean logic:
*eligible data breach = covered AND element 1 AND element 2 AND NOT exception*.

### Technical design
| Technique | Where it is used |
|---|---|
| Structured (JSON) outputs | Every legal step returns true/false, confidence, reasoning and citations |
| Retrieval-augmented generation | Each step retrieves the most relevant passages from Part 4 of the OAIC guide (semantic search with OpenAI embeddings, restricted to the sections relevant to that step) |
| If-then legal logic | Rule-based conclusion computed in Python, not by the AI |
| Reflection with looping | A senior-reviewer step can send flawed steps back with feedback; they are re-run and re-reviewed (up to 2 revision rounds) |
| Document generation | Advice memo and, for notifiable breaches, a draft s 26WK statement (.docx) |

Each run makes **at least 7 AI calls** (more when steps are revised or a statement is drafted).

### Known limitations
- Only as good as the facts given; missing facts are flagged but not investigated.
- "Serious harm" is evaluative; results on borderline facts can vary between runs.
- The reviewer can disagree with the rule-based result; both are shown so the user can judge.
- Coverage rules are summarised rather than quoted, and the OAIC guide used is the July 2019 edition.
- Exceptions to notification (e.g. enforcement bodies, secrecy provisions, My Health Records)
  are not assessed.
"""
)
