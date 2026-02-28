import streamlit as st
from pages.login import show_login
from pages.dashboard import show_dashboard

st.set_page_config(page_title="FinSight AI", layout="centered")

# 🔹 Load global CSS here
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Routing
if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
