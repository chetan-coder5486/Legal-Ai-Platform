import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), encoding="utf-8")

# ─── Lazy-loaded Groq client ──────────────────────────────────────────────
_client = None
_api_available = None


def _get_client():
    """Lazy-load the Groq client. Returns None if API key is missing."""
    global _client, _api_available

    if _api_available is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[explainability] WARNING: GROQ_API_KEY not set — explanations will use fallback text.")
            _api_available = False
        else:
            try:
                from groq import Groq
                _client = Groq(api_key=api_key)
                _api_available = True
            except Exception as e:
                print(f"[explainability] WARNING: Could not initialise Groq client: {e}")
                _api_available = False

    return _client


def generate_explanation(risk_analysis: dict) -> dict:
    """
    Uses Groq (free) to generate plain-English clause explanations.
    Model: llama-3.1-8b-instant — fast, free, 14400 requests/day

    Falls back to a basic risk summary if the API key is missing or the call fails.
    """
    clause_text = risk_analysis.get("clause_text", "")
    clause_type = risk_analysis.get("type", "Unknown")
    risk_level  = risk_analysis.get("risk_level", "LOW")
    risk_reason = risk_analysis.get("risk_reason", "")

    client = _get_client()

    if client is None:
        # No API key — use fallback without crashing
        risk_analysis["explanation"] = (
            f"Clause flagged as {risk_level} RISK.\n"
            f"Reason: {risk_reason}"
        )
        return risk_analysis

    prompt = f"""You are a legal analyst reviewing an NDA (Non-Disclosure Agreement).

Clause type: {clause_type}
Risk level: {risk_level}
Risk reason: {risk_reason}

Clause text:
\"\"\"{clause_text[:400]}\"\"\"

Write exactly 2-3 sentences in plain English explaining:
1. What this clause means in simple terms
2. Why the risk level is {risk_level}
3. One specific thing the signing party should watch out for

Be concise and practical. No legal jargon."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a concise legal analyst. Always respond in 2-3 plain English sentences."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=200,
            temperature=0.3
        )
        explanation = response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[explainability] Groq API call failed: {e}")
        explanation = (
            f"Clause flagged as {risk_level} RISK.\n"
            f"Reason: {risk_reason}"
        )

    risk_analysis["explanation"] = explanation
    return risk_analysis
