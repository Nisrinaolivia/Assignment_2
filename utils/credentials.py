"""
API credentials sidebar module.

Based on the course module: https://github.com/stoneman-mls/openai_credentials
Users enter their own OpenAI API key, which is stored in
st.session_state.openai_api_key for the current browser session only.

Adaptations from the original:
- wrapped in credentials_sidebar() so it appears on every page;
- the key input is masked, and only the last 4 characters are displayed;
- optional access password: users without an API key can enter a password to use
  the app owner's key. The password and key are stored in Streamlit Secrets
  (never in this repository), and runs per session are capped in utils/llm.py.
"""

import hmac

import streamlit as st


def _get_secret(name):
    """Returns a value from Streamlit Secrets, or None if secrets are not set up."""
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def render_sidebar():
    st.sidebar.title("API Key Input")
    api_key = st.sidebar.text_input("Enter your API key:", type="password")
    update_button = st.sidebar.button("Update API Key")
    return api_key, update_button


def render_password_option():
    """Lets users without an API key unlock the app with an access password."""
    app_password = _get_secret("APP_PASSWORD")
    shared_key = _get_secret("SHARED_OPENAI_API_KEY")
    if not (app_password and shared_key):
        return  # password access is not set up, so the option is hidden

    st.sidebar.divider()
    st.sidebar.subheader("No API key?")
    password = st.sidebar.text_input("Enter access password:", type="password")
    if st.sidebar.button("Unlock"):
        if hmac.compare_digest(password, app_password):
            st.session_state.openai_api_key = shared_key
            st.session_state.using_shared_key = True
        else:
            st.sidebar.error("Incorrect password.")


def credentials_sidebar():
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = None
    if "using_shared_key" not in st.session_state:
        st.session_state.using_shared_key = False

    api_key, update_button = render_sidebar()
    if update_button:
        st.session_state.openai_api_key = api_key
        st.session_state.using_shared_key = False

    render_password_option()

    key = st.session_state.openai_api_key
    if key and st.session_state.using_shared_key:
        st.sidebar.success("Access granted via password.")
    elif key:
        st.sidebar.caption(f"Current API Key: ••••{key[-4:]}")
    else:
        st.sidebar.caption("Current API Key: None")