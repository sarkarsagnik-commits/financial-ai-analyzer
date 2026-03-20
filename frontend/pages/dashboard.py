import streamlit as st
import requests
from utils.ui import analysis_card, result_card
from utils.jwt_handler import get_auth_headers, clear_token
from config import API_BASE_URL


def show_dashboard():
    # ── Header ────────────────────────────────────────────────────────────
    col_title, col_logout = st.columns([6, 1])
    with col_title:
        st.markdown("## FinSight AI — Dashboard")
    with col_logout:
        if st.button("Logout"):
            clear_token()
            st.rerun()

    st.markdown("---")

    # ── Upload ────────────────────────────────────────────────────────────
    st.markdown("### Upload Financial Report")
    uploaded_file = st.file_uploader(
        "Drag & drop your PDF here or click to browse",
        type=["pdf"],
    )

    document_id = st.session_state.get("document_id")

    if uploaded_file and st.button("Upload & Index Document", use_container_width=True):
        with st.spinner("Uploading and indexing document..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/api/upload/",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                    headers=get_auth_headers(),
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state["document_id"] = data["document_id"]
                    document_id = data["document_id"]
                    st.success(
                        f"Indexed **{data['filename']}** — "
                        f"{data['page_count']} pages, {data['chunks_stored']} chunks stored."
                    )
                else:
                    st.error(f"Upload failed: {resp.json().get('detail', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach backend. Start FastAPI with: `uvicorn main:app --reload`")

    if document_id:
        st.info(f"Active document ID: `{document_id}`")

    st.markdown("---")

    # ── Module selection ───────────────────────────────────────────────────
    st.markdown("### Select Analysis Modules")
    col1, col2, col3 = st.columns(3)

    with col1:
        financial_changes = analysis_card(
            title="Financial Changes",
            description="Extract key financial metrics and compute year-over-year changes.",
        )
    with col2:
        risk_radar = analysis_card(
            title="Risk Radar",
            description="Identify and summarize major risk factors from the filing.",
        )
    with col3:
        management_outlook = analysis_card(
            title="Management Outlook",
            description="Analyze tone and forward-looking guidance from management.",
        )

    st.markdown("")

    # ── Run analysis ───────────────────────────────────────────────────────
    if st.button("Run Analysis", use_container_width=True):
        if not document_id:
            st.warning("Please upload and index a document first.")
        else:
            selected_modules = []
            if financial_changes:
                selected_modules.append("Financial Changes")
            if risk_radar:
                selected_modules.append("Risk Radar")
            if management_outlook:
                selected_modules.append("Management Outlook")

            if not selected_modules:
                st.warning("Select at least one analysis module.")
            else:
                with st.spinner(f"Running: {', '.join(selected_modules)}..."):
                    try:
                        resp = requests.post(
                            f"{API_BASE_URL}/api/analysis/run",
                            json={"document_id": document_id, "modules": selected_modules},
                            headers={**get_auth_headers(), "Content-Type": "application/json"},
                            timeout=120,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state["analysis_results"] = data
                            st.success("Analysis complete!")
                        else:
                            st.error(f"Analysis failed: {resp.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot reach backend.")

    # ── Results display ────────────────────────────────────────────────────
    if "analysis_results" in st.session_state:
        results = st.session_state["analysis_results"].get("results", {})
        st.markdown("---")
        st.markdown("### Analysis Results")

        for module_name, result in results.items():
            with st.expander(f"📊 {module_name}", expanded=True):
                if "error" in result:
                    st.error(result["error"])
                    continue

                if module_name == "Financial Changes":
                    st.markdown("**Key Metrics**")
                    st.json(result.get("metrics", {}))
                    result_card("Summary", result.get("summary", ""))
                    if "context_preview" in result:
                        st.caption("Context preview: " + result["context_preview"])

                elif module_name == "Risk Radar":
                    st.markdown("**Risk Severity Breakdown**")
                    breakdown = result.get("severity_breakdown", {})
                    if breakdown:
                        st.bar_chart(breakdown)
                    for risk in result.get("risk_factors", []):
                        result_card(risk["type"], risk.get("excerpt", ""))
                    result_card("Summary", result.get("summary", ""))

                elif module_name == "Management Outlook":
                    tone = result.get("tone", "N/A")
                    score = result.get("tone_score", 0)
                    st.metric("Tone", tone, delta=f"Score: {score:.0%}")
                    st.markdown("**Key Themes**")
                    st.write(", ".join(result.get("key_themes", [])))
                    st.markdown("**Forward-Looking Statements**")
                    for stmt in result.get("forward_guidance", []):
                        st.markdown(f"- {stmt}")
                    result_card("Summary", result.get("summary", ""))

    # ── Semantic search ────────────────────────────────────────────────────
    if document_id:
        st.markdown("---")
        st.markdown("### Semantic Document Search")
        query = st.text_input("Ask a question about the document", placeholder="What were the main revenue drivers?")
        if st.button("Search", key="semantic_search") and query:
            with st.spinner("Searching..."):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/api/analysis/query",
                        json={"document_id": document_id, "query": query, "top_k": 5},
                        headers={**get_auth_headers(), "Content-Type": "application/json"},
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        chunks = resp.json().get("results", [])
                        for i, chunk in enumerate(chunks, 1):
                            result_card(f"Result {i}", chunk)
                    else:
                        st.error("Search failed.")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot reach backend.")