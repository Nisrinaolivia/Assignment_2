"""Helper for calling the OpenAI API. Every call is counted so the UI can show
that the app makes at least 5 AI calls per run."""

import json

import streamlit as st
from openai import OpenAI

MODEL = "gpt-4o-mini"

# Maximum number of assessments per browser session when using the shared
# (password-protected) key, to limit cost to the app owner.
MAX_SHARED_RUNS = 5


def get_client():
    # The key only ever comes from the sidebar (own key or password unlock).
    key = st.session_state.get("openai_api_key")
    if not key:
        st.error("Please enter your OpenAI API key or the access password in the sidebar.")
        st.stop()
    if st.session_state.get("using_shared_key"):
        runs = st.session_state.get("shared_runs", 0)
        if runs >= MAX_SHARED_RUNS:
            st.error(
                f"You have reached the limit of {MAX_SHARED_RUNS} assessments for this session. "
                "Please enter your own OpenAI API key in the sidebar to continue."
            )
            st.stop()
        st.session_state["shared_runs"] = runs + 1
    return OpenAI(api_key=key)


def ask(client, system: str, user: str, as_json: bool = False):
    """One AI call. Returns text, or a dict when as_json=True."""
    kwargs = {}
    if as_json:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        **kwargs,
    )
    st.session_state["ai_calls"] = st.session_state.get("ai_calls", 0) + 1
    content = resp.choices[0].message.content
    return json.loads(content) if as_json else content