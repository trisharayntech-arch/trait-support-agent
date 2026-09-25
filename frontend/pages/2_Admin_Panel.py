"""Admin panel: knowledge-base document management and escalation review."""
import streamlit as st
from api_client import (
    delete_document,
    list_documents,
    list_escalations,
    resolve_escalation,
    upload_document,
)

st.set_page_config(page_title="Admin Panel", page_icon="🛠️", layout="wide")
st.title("🛠️ Admin Panel")

with st.sidebar:
    st.subheader("Admin authentication")
    admin_key = st.text_input("Admin API Key", type="password")
    st.caption("This must match ADMIN_API_KEY in the backend's .env file.")

if not admin_key:
    st.info("Enter the admin API key in the sidebar to continue.")
    st.stop()

tab_docs, tab_escalations = st.tabs(["📄 Knowledge Base", "🚨 Escalations"])

with tab_docs:
    st.subheader("Upload a document")
    uploaded_file = st.file_uploader("Choose a PDF, TXT, or DOCX file", type=["pdf", "txt", "docx"])
    if uploaded_file is not None and st.button("Upload and Index"):
        with st.spinner("Processing document..."):
            try:
                result = upload_document(admin_key, uploaded_file.name, uploaded_file.getvalue())
                st.success(result["message"])
                st.json(result["document"])
            except Exception as exc:  # noqa: BLE001
                st.error(f"Upload failed: {exc}")

    st.divider()
    st.subheader("Indexed documents")
    if st.button("Refresh list"):
        st.rerun()

    try:
        docs = list_documents(admin_key)
        if not docs:
            st.write("No documents uploaded yet.")
        for doc in docs:
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 1])
            col1.write(doc["filename"])
            col2.write(doc["file_type"])
            col3.write(f"{doc['chunk_count']} chunks")
            col4.write(doc["status"])
            if col5.button("Delete", key=f"del_{doc['id']}"):
                try:
                    delete_document(admin_key, doc["id"])
                    st.success(f"Deleted '{doc['filename']}'.")
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Delete failed: {exc}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load documents: {exc}")

with tab_escalations:
    st.subheader("Open escalations")
    status_filter = st.selectbox("Filter by status", ["open", "resolved", "all"])
    filter_value = None if status_filter == "all" else status_filter

    try:
        escalations = list_escalations(admin_key, filter_value)
        if not escalations:
            st.write("No escalations found.")
        for esc in escalations:
            with st.container(border=True):
                st.write(f"**Escalation #{esc['id']}** — session `{esc['session_id']}`")
                st.write(f"Reason: {esc['reason']}")
                if esc.get("last_customer_message"):
                    st.caption(f"Last customer message: {esc['last_customer_message']}")
                st.write(f"Status: {esc['status']} | Created: {esc['created_at']}")
                if esc["status"] == "open" and st.button("Mark resolved", key=f"resolve_{esc['id']}"):
                    try:
                        resolve_escalation(admin_key, esc["id"])
                        st.success("Marked resolved.")
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Could not resolve: {exc}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load escalations: {exc}")
