import streamlit as st
import requests


API_URL = "http://127.0.0.1:8000/orchestrator/assign_agent"
CONTEXT_API_URL = "http://127.0.0.1:8000/orchestrator/agents/context"


def chat_with_agent():
    st.write("Ask the AI agent for advice, agent assignment, or route suggestions:")

    user_input = st.text_input("Your question / order id:")
    
    # ✅ NEW: Add debug mode toggle
    col1, col2 = st.columns(2)
    with col1:
        use_rag = st.checkbox("Use Smart Memory (RAG)", value=True)
    with col2:
        debug_mode = st.checkbox("🔍 Show RAG Debug Info", value=True)
    
    if st.button("Send") and user_input:
        # For agent assignment request
        if user_input.lower().startswith("assign"):
            order_id = user_input.split(" ")[-1]
            try:
                response = requests.post(f"{API_URL}/{order_id}")
                data = response.json()
                st.write(data)
            except Exception as e:
                st.error(f"Error calling backend: {e}")
        else:
            # Generic question -> use local Groq LLM with optional RAG context
            from components.llm_agent import llm_client

            try:
                # ✅ NEW: Show RAG context retrieval process
                if debug_mode and use_rag:
                    st.markdown("---")
                    st.subheader("🔍 RAG Debug Information")
                    
                    # Step 1: Show what context is being retrieved
                    with st.spinner("Retrieving context from Neo4j..."):
                        try:
                            context_response = requests.post(
                                CONTEXT_API_URL,
                                json={"query": user_input},
                                timeout=5
                            )
                            if context_response.status_code == 200:
                                context_data = context_response.json()
                                
                                # Display entities detected
                                st.markdown("**📋 Entities Detected:**")
                                entities = context_data.get("entities_detected", {})
                                if any(entities.values()):
                                    cols = st.columns(len([k for k, v in entities.items() if v]))
                                    col_idx = 0
                                    for key, value in entities.items():
                                        if value:
                                            with cols[col_idx]:
                                                st.metric(key.replace("_", " ").title(), value)
                                            col_idx += 1
                                else:
                                    st.info("No specific entities detected")
                                
                                # Display retrieved context
                                context_text = context_data.get("context", "")
                                st.markdown("**📚 Knowledge Retrieved from Neo4j:**")
                                if context_text and context_text.strip():
                                    st.success("✅ Context Found!")
                                    with st.expander("View Retrieved Context", expanded=True):
                                        st.write(context_text)
                                        st.caption(f"📊 Context length: {len(context_text)} characters")
                                else:
                                    st.warning("⚠️ No historical context found (first time query or no matching data)")
                                
                                # Display keywords
                                keywords = context_data.get("keywords", [])
                                if keywords:
                                    st.markdown("**🔑 Keywords Extracted:**")
                                    st.write(", ".join(keywords))
                                
                        except Exception as e:
                            st.error(f"❌ Failed to retrieve context: {e}")
                    
                    st.markdown("---")
                
                # Generate answer from Groq
                st.markdown("### 💬 AI Response")
                with st.spinner("Generating answer..."):
                    answer = llm_client.chat(user_input, use_rag=use_rag)
                
                # ✅ NEW: Highlight if RAG was used
                if use_rag:
                    st.info("🧠 Answer generated using RAG (with Neo4j context)")
                else:
                    st.info("🤖 Answer generated without RAG (generic response)")
                
                st.markdown(f"**Answer:** {answer}")
                
                # ✅ NEW: Show comparison tip
                if debug_mode:
                    with st.expander("💡 Tip: Test RAG Effectiveness"):
                        st.write("""
                        **To verify RAG is working:**
                        1. Ask the same question twice
                        2. First time: No context found
                        3. Second time: Context should appear above
                        4. Answer should reference "previous reports" or "commonly asked"
                        
                        **Try these test queries:**
                        - "Why does Yonex string break?"
                        - "Yonex string problem" (ask again)
                        - Compare the context retrieved!
                        """)
            
            except Exception as e:
                st.error(f"Groq error: {e}")
                import traceback
                if debug_mode:
                    st.code(traceback.format_exc())
