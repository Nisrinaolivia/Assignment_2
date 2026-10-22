# Notifiable Data Breach Checker

LAWS90286 Legal AI: Design and Development, Assignment 2.

An AI-powered Streamlit app that assesses whether a data incident is an **eligible data breach**
that must be notified under Part IIIC of the *Privacy Act 1988* (Cth) (the Notifiable Data
Breaches scheme), and drafts the advice memo and the statement to the Commissioner.

**Deployed app:** <PASTE STREAMLIT CLOUD URL HERE>

## How to use
1. Open the app and enter your OpenAI API key in the sidebar, then click **Update API Key**
   (or use the access password, if you were given one).
2. Go to **Breach Assessment**.
3. Load a test case from the dropdown, upload an incident report (.txt, .docx or .pdf), or type your own.
4. Click **Assess** and review the results in the tabs.

## What the app does
| # | Step | Technique |
|---|---|---|
| 1 | Extract facts and flag missing facts | Structured JSON output |
| 2 | Coverage: is the entity / information covered by the NDB scheme? | RAG over the OAIC guide |
| 3 | Element 1: unauthorised access, disclosure or loss (s 26WE(2)) | RAG + statute |
| 4 | Element 2: likely serious harm, each s 26WG matter assessed separately | RAG + statute |
| 5 | Exception: remedial action (s 26WF) | RAG + statute |
| – | Rule-based conclusion: *covered AND E1 AND E2 AND NOT exception* | If-then logic in Python |
| 6 | Senior review; flawed steps are sent back with feedback and re-run (max 2 rounds) | Reflection + looping |
| 7 | Advice memo with OAIC citations (.docx download) | Generation |
| 8 | Draft s 26WK statement to the Commissioner, only if notifiable (.docx download) | RAG + generation |

Each run makes **at least 7 AI calls**. The legal data used is the statutory text of ss 6(1), 26WE,
26WF and 26WG (`knowledge/ndb_law.py`) and Part 4 of the OAIC's *Data breach preparation and
response* guide, split into 104 cited passages (`knowledge/oaic_guide.json`).

## Test cases
Load each case from the **Load a test case** dropdown (the text is also in `test_files/`).
Results from AI models vary between runs, so the expected results below describe what a correct
analysis should conclude and what each case is designed to show.

### Test case 1: Hacked dental patient database (`test_files/scenario_1.txt`)
**Designed to show:** the full "notifiable" path, including the draft statement to the OAIC.

| Step | Expected result |
|---|---|
| Coverage | ✅ Covered: APP entity (turnover about $8m) and a health service provider |
| Element 1 | ✅ Unauthorised access (external attacker) |
| Element 2 | ✅ Serious harm likely: health and Medicare data, unencrypted, 40,000 people, offered for sale |
| Remedial action | Exception does not apply: patching does not retrieve data already on the dark web |
| **Conclusion** | 🚨 **Eligible data breach** |

**What to check:** the *Serious harm factors* tab shows each s 26WG matter; the *OAIC statement*
tab contains a draft s 26WK statement with `[to be confirmed]` placeholders rather than invented
contact details; both Word documents download.

### Test case 2: Lost encrypted laptop, remotely wiped (`test_files/scenario_2.txt`)
**Designed to show:** that a breach can fall outside the scheme because of security measures and
prompt remedial action (mirrors OAIC guide examples at pp 33, 37).

| Step | Expected result |
|---|---|
| Coverage | ✅ Covered: APP entity (energy retailer, turnover about $45m) |
| Element 1 | ❌ or borderline: lost, but unauthorised access is unlikely (strong encryption, wiped within 30 minutes) |
| Element 2 | ❌ Serious harm not likely, despite bank details, because of encryption |
| Remedial action | ⚠️ Exception applies: wiped before any access, confirmed by logs |
| **Conclusion** | ✅ **Not an eligible data breach** |

**What to check:** the reasoning cites the OAIC guidance on encryption and remote deletion; no
statement is drafted; the memo recommends documenting the assessment.

### Test case 3: Misdirected tax return, small accounting firm (`test_files/scenario_3.txt`)
**Designed to show:** nuanced coverage and the limits of the tool on an evaluative, borderline
judgment.

| Step | Expected result |
|---|---|
| Coverage | ◐ **Partly covered**: a small business (turnover $1.6m) is not an APP entity, but as a TFN recipient it is covered for the **TFN information** |
| Element 1 | ✅ Unauthorised disclosure (email to the wrong person) |
| Element 2 | Likely ✅: TFN, income and bank details enable identity fraud |
| Remedial action | **Contestable**: the recipient says it deleted the email, but this cannot be verified and there is no confidentiality contract (compare OAIC Example 6 at p 41, where written assurance and a contract were enough) |
| **Conclusion** | ⚠️ **Uncertain** or 🚨 **Eligible**; reasonable lawyers could differ |

**What to check / known limitation:** run this case two or three times. The coverage step should
pick up the TFN rule; the remedial-action step and the final conclusion may change between runs.
The *Review loop* tab often shows the reviewer challenging the remedial-action step. This
illustrates that the tool is reliable on clear facts but less consistent where the law requires an
evaluative judgment, which is where human review remains essential.

## Run locally
```bash
pip install -r requirements.txt
streamlit run Home.py
```
Optional password access: create `.streamlit/secrets.toml` (never commit it) containing
`APP_PASSWORD = "..."` and `SHARED_OPENAI_API_KEY = "..."`.

## Structure
```
Home.py                       landing page
pages/1_Breach_Assessment.py  the tool (input, results tabs, downloads)
pages/2_About.py              legal and technical design, limitations
utils/credentials.py          API key sidebar (course module) + optional password
utils/llm.py                  OpenAI chat calls (counted)
utils/pipeline.py             the assessment steps, rule-based logic and review loop
utils/retrieval.py            RAG over the OAIC guide (embeddings, keyword fallback)
utils/prompts.py              prompts for each step
utils/export.py               Word (.docx) memo and statement
knowledge/ndb_law.py          statutory text and coverage summary
knowledge/oaic_guide.json     OAIC guide Part 4, split into cited passages
test_files/                   the three test cases
```

## Sources
- *Privacy Act 1988* (Cth), Part IIIC (Federal Register of Legislation).
- Office of the Australian Information Commissioner, *Data breach preparation and response: A guide
  to managing data breaches in accordance with the Privacy Act 1988 (Cth)* (July 2019), Part 4.

*Not legal advice.*
