import streamlit as st
from utils.auth import authenticate_user
from utils.ui import render_logo

def show_login():
    st.markdown("<h1 style='text-align:center;'>FinSight AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>AI-powered analysis for 10-K and 10-Q filings</p>", unsafe_allow_html=True)
    
    st.markdown("## Sign in to your account")

    email = st.text_input("Email address", placeholder="you@company.com")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if authenticate_user(email, password):
            st.session_state.authenticated = True
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown("Don't have an account? **Create Account**")
