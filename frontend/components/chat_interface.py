import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/orchestrator/assign_agent"  # Or LLM endpoint

def chat_with_agent():
    st.write("Ask the AI agent for advice, agent assignment, or route suggestions:")

    user_input = st.text_input("Your question / order id:")
    if st.button("Send") and user_input:
        # For agent assignment request
        if user_input.lower().startswith("assign"):
            order_id = user_input.split(" ")[-1]  # simple parsing
            try:
                response = requests.post(f"{API_URL}/{order_id}")
                data = response.json()
                st.write(data)
            except Exception as e:
                st.error(f"Error calling backend: {e}")
        else:
            # Generic question -> call LLM via backend API
            try:
                response = requests.post("http://127.0.0.1:8000/orchestrator/chat", json={"message": user_input})
                data = response.json()
                st.write(data.get("response", "No response from AI"))
            except Exception as e:
                st.error(f"Error calling AI backend: {e}")
