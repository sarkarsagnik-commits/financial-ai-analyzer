import streamlit as st
from utils.ui import analysis_card

def show_dashboard():
    st.markdown("## Upload Financial Report")

    uploaded_file = st.file_uploader(
        "Drag & drop your PDF here or click to browse",
        type=["pdf"]
    )

    st.markdown("---")
    st.markdown("## Select Analysis Modules")

    col1, col2, col3 = st.columns(3)

    with col1:
        financial_changes = analysis_card(
            title="Financial Changes",
            description="Extract key financial metrics and compute year-over-year changes."
        )

    with col2:
        risk_radar = analysis_card(
            title="Risk Radar",
            description="Identify and summarize major risk factors from the filing."
        )

    with col3:
        management_outlook = analysis_card(
            title="Management Outlook",
            description="Analyze tone and forward-looking guidance from management."
        )

    st.markdown("")

    if st.button("Run Analysis", use_container_width=True):
        if not uploaded_file:
            st.warning("Please upload a PDF first.")
        else:
            selected = []
            if financial_changes:
                selected.append("Financial Changes")
            if risk_radar:
                selected.append("Risk Radar")
            if management_outlook:
                selected.append("Management Outlook")

            st.success(f"Running analysis for: {selected}")
