# frontend/components/llm_agent.py
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

# === Load .env variables ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

# === Environment variables ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# === Supported fallback models (Updated November 2024) ===
SUPPORTED_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-groq-70b-8192-tool-use-preview",
    "llama3-groq-8b-8192-tool-use-preview",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


class GroqClient:
    def __init__(self, api_key=GROQ_API_KEY, model=GROQ_MODEL):
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY missing in .env")
        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

        # Verify model validity
        if model not in SUPPORTED_MODELS:
            print(f"[WARN] {model} not supported → switching to {SUPPORTED_MODELS[0]}")
            model = SUPPORTED_MODELS[0]
        self.model = model
        print(f"[INFO] ✅ Using Groq model: {self.model}")

    def chat(self, prompt: str, use_rag: bool = True):
        """Send message to Groq API with optional context retrieval."""
        
        # ✅ FIXED: Retrieve RAG context from backend
        rag_context = ""
        if use_rag:
            try:
                print(f"[DEBUG] Fetching RAG context from backend...")
                rag_resp = requests.post(
                    f"{BACKEND_URL}/orchestrator/agents/context",
                    json={"query": prompt},
                    timeout=5,
                )
                if rag_resp.status_code == 200:
                    data = rag_resp.json()
                    # ✅ Get the context string, not a list
                    rag_context = data.get("context", "")
                    print(f"[DEBUG] RAG Context retrieved: {rag_context[:200]}...")
                else:
                    print(f"[WARN] RAG endpoint returned status {rag_resp.status_code}")
            except Exception as e:
                print(f"[WARN] Could not fetch RAG context: {e}")

        # ✅ Build enhanced system prompt with context
        system_prompt = """You are a professional badminton racket stringing expert with years of experience. 
You provide concise, practical advice based on real-world experience and common issues."""

        if rag_context:
            system_prompt += f"""

HISTORICAL KNOWLEDGE FROM DATABASE:
{rag_context}

Use this historical data to inform your answer. If similar issues have been reported before, mention that naturally."""

        # Query Groq
        try:
            print(f"[DEBUG] Sending to Groq with model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,  # ✅ Slightly higher for more natural responses
                max_tokens=500,   # ✅ Increased for better answers
            )
            answer = response.choices[0].message.content.strip()
            print(f"[DEBUG] ✅ Got response from Groq ({len(answer)} chars)")
            return answer
        
        # Handle errors
        except Exception as e:
            err_msg = str(e)
            print(f"[ERROR] Groq API error: {err_msg}")

            # Prevent infinite recursion: limit fallback attempts
            if hasattr(self, "_fallback_attempted") and self._fallback_attempted:
                return f"[Groq Error] {err_msg}"
            self._fallback_attempted = True

            if "model_not_found" in err_msg or "model_decommissioned" in err_msg:
                for alt in SUPPORTED_MODELS:
                    if alt != self.model:
                        print(f"[INFO] Switching to alternate Groq model: {alt}")
                        self.model = alt
                        try:
                            return self.chat(prompt, use_rag=False)
                        except Exception as inner_e:
                            return f"[Groq Error] {inner_e}"
            return f"[Groq Error] {err_msg}"

print(f"[DEBUG] GROQ_MODEL (env): {GROQ_MODEL}")
print(f"[DEBUG] Supported models: {SUPPORTED_MODELS}")

# === Initialize client ===
llm_client = GroqClient()