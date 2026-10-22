"""Helper for calling the OpenAI API. Every call is counted so the UI can show
that the app makes at least 5 AI calls per run."""

import json

import streamlit as st
from openai import OpenAI

DEFAULT_MODEL = "gpt-4o-mini"

# Models users can choose from (all support JSON output and the temperature setting).
MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o", "gpt-4.1"]

# Users who unlock the app with the shared password can only use the standard model,
# to keep the app owner's costs down.
SHARED_MODELS = ["gpt-4o-mini"]

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


def ask(client, system: str, user: str, as_json: bool = False, model: str = DEFAULT_MODEL):
    """One AI call. Returns text, or a dict when as_json=True."""
    kwargs = {}
    if as_json:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(
        model=model,
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


def friendly_error(err):
    """Turns an OpenAI error into a plain-English message for non-technical users."""
    text = str(err).lower()
    shared = st.session_state.get("using_shared_key")
    if "model_not_found" in text or "does not have access to model" in text:
        if shared:
            return ("This AI model is not available with password access. "
                    "Please choose **gpt-4o-mini** under Settings and try again.")
        return ("Your OpenAI account does not have access to this AI model. "
                "Please choose another model under Settings (gpt-4o-mini works for most accounts).")
    if "invalid_api_key" in text or "incorrect api key" in text or "401" in text:
        return ("Your OpenAI API key was not accepted. Please check that you copied the whole key, "
                "then click **Update API Key** again.")
    if "insufficient_quota" in text or "exceeded your current quota" in text:
        return ("The OpenAI account has run out of credit. If you are using your own key, please add "
                "credit in your OpenAI account; if you used the password, please contact the app owner.")
    if "rate_limit" in text or "429" in text:
        return "Too many requests were sent at once. Please wait a minute and try again."
    if "timeout" in text or "connection" in text:
        return "The connection to OpenAI was interrupted. Please check your internet connection and try again."
    return "Something went wrong while contacting OpenAI. Please try again in a moment."
