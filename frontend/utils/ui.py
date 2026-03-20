import streamlit as st


def render_logo():
    st.markdown(
        "<div style='text-align:center;font-size:2.5rem;font-weight:800;letter-spacing:-1px;'>FinSight AI</div>",
        unsafe_allow_html=True,
    )


def analysis_card(title: str, description: str) -> bool:
    """Renders a styled toggle card. Returns True if selected."""
    key = f"card_{title.lower().replace(' ', '_')}"
    if key not in st.session_state:
        st.session_state[key] = False

    selected = st.session_state[key]
    border_color = "#4F8EF7" if selected else "#2a2a3d"
    bg_color = "#1a2340" if selected else "#12121f"

    st.markdown(
        f"""
        <div style="
            border: 2px solid {border_color};
            border-radius: 10px;
            padding: 16px;
            background: {bg_color};
            margin-bottom: 4px;
            transition: all 0.2s;
        ">
            <strong style="font-size:1rem;">{title}</strong>
            <p style="font-size:0.82rem; color:#9a9ab0; margin:6px 0 0 0;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    toggled = st.checkbox("Enable", key=key, value=selected, label_visibility="collapsed")
    return toggled


def result_card(title: str, content: str):
    st.markdown(
        f"""
        <div style="
            border: 1px solid #2a2a3d;
            border-radius: 10px;
            padding: 18px;
            background: #12121f;
            margin-bottom: 12px;
        ">
            <h4 style="margin:0 0 8px 0; color:#4F8EF7;">{title}</h4>
            <p style="margin:0; font-size:0.88rem; color:#c0c0d0; white-space: pre-wrap;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )