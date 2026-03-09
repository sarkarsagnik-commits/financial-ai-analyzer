import streamlit as st
from utils.auth import authenticate_user, register_user
from utils.ui import render_logo


def show_login():
    render_logo()
    st.markdown(
        "<p style='text-align:center; color:#9a9ab0;'>AI-powered analysis for 10-K and 10-Q filings</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    tab1, tab2 = st.tabs(["Sign In", "Create Account"])

    with tab1:
        st.markdown("### Sign in to your account")
        email = st.text_input("Email address", placeholder="you@company.com", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True, key="login_btn"):
            if not email or not password:
                st.warning("Please enter your email and password.")
            else:
                with st.spinner("Authenticating..."):
                    result = authenticate_user(email, password)
                if result["ok"]:
                    st.session_state.authenticated = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result["error"])

    with tab2:
        st.markdown("### Create a new account")
        new_name = st.text_input("Full name", placeholder="Jane Smith", key="reg_name")
        new_email = st.text_input("Email address", placeholder="you@company.com", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")

        if st.button("Create Account", use_container_width=True, key="reg_btn"):
            if not new_email or not new_password:
                st.warning("Email and password are required.")
            else:
                with st.spinner("Creating account..."):
                    result = register_user(new_email, new_password, new_name)
                if result["ok"]:
                    st.session_state.authenticated = True
                    st.success("Account created!")
                    st.rerun()
                else:
                    st.error(result["error"])