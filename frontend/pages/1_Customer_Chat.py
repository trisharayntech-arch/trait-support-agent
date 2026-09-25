"""Customer-facing chat page."""
import uuid

import streamlit as st
from api_client import request_escalation, send_chat_message

st.set_page_config(page_title="Customer Chat", page_icon="💬")
st.title("💬 Customer Support Chat")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": ..., "content": ...}

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources used"):
                for s in msg["sources"]:
                    st.caption(
                        f"**{s['document_name']}** (similarity: {s['similarity_score']:.2f})"
                    )
                    st.text(s["chunk_preview"])
        if msg.get("escalation_suggested"):
            if st.button("Talk to a human agent", key=f"escalate_{len(st.session_state.messages)}"):
                try:
                    result = request_escalation(
                        st.session_state.session_id, "Customer requested escalation from chat UI"
                    )
                    st.success(f"Escalation created (ID {result['id']}). A human agent will follow up.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not create escalation: {exc}")

user_input = st.chat_input("Ask a question about our products, policies, or support...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = send_chat_message(st.session_state.session_id, user_input)
                st.markdown(result["answer"])
                confidence_pct = result["confidence_score"] * 100
                st.caption(f"Confidence: {confidence_pct:.0f}%")

                if result.get("sources"):
                    with st.expander("Sources used"):
                        for s in result["sources"]:
                            st.caption(
                                f"**{s['document_name']}** (similarity: {s['similarity_score']:.2f})"
                            )
                            st.text(s["chunk_preview"])

                if result.get("escalation_suggested"):
                    st.warning(
                        "This answer has low confidence. You can request a human agent below."
                    )
                    if st.button("Talk to a human agent", key="escalate_latest"):
                        try:
                            esc = request_escalation(
                                st.session_state.session_id,
                                "Customer requested escalation from chat UI",
                            )
                            st.success(f"Escalation created (ID {esc['id']}).")
                        except Exception as exc:  # noqa: BLE001
                            st.error(f"Could not create escalation: {exc}")

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result.get("sources", []),
                        "escalation_suggested": result.get("escalation_suggested", False),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Error contacting the support agent: {exc}")
