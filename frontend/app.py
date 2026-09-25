"""Streamlit multipage app entrypoint for the TRAIT AI Customer Support Agent."""
import streamlit as st

from api_client import check_health

st.set_page_config(page_title="TRAIT AI Support Agent", page_icon="💬", layout="wide")

st.title("💬 TRAIT AI Customer Support Agent")
st.write(
    "Use the sidebar to navigate to **Customer Chat** (talk to the support agent) "
    "or **Admin Panel** (manage the knowledge base and review escalations)."
)

st.subheader("Backend status")
try:
    health = check_health()
    st.success(f"Backend reachable. Indexed chunks: {health.get('indexed_chunk_count')}")
except Exception as exc:  # noqa: BLE001
    st.error(f"Backend not reachable: {exc}")
    st.info("Make sure the FastAPI backend is running (see README.md).")
