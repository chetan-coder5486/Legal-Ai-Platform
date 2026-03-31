import os
import anthropic
from dotenv import load_dotenv

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_explanation(risk_analysis: dict) -> dict:
    """
    Uses Claude to generate a plain-English explanation for each clause.
    Replaces the old hardcoded 'Standard language detected' message.
    """
    clause_text = risk_analysis.get("clause_text", "")
    clause_type = risk_analysis.get("type", "Unknown")
    risk_level  = risk_analysis.get("risk_level", "LOW")
    risk_reason = risk_analysis.get("risk_reason", "")

    # Build a focused prompt for Claude
    prompt = f"""You are a legal analyst reviewing an NDA (Non-Disclosure Agreement).

Clause type: {clause_type}
Risk level:  {risk_level}
Risk reason: {risk_reason}

Clause text:
\"\"\"{clause_text}\"\"\"

Write a 2-3 sentence plain-English explanation of:
1. What this clause means in simple terms
2. Why the risk level is {risk_level}
3. One specific thing the signing party should watch out for

Be concise and practical. Do not use legal jargon. Write as if explaining to a business owner."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",  # fast + cheap for per-clause calls
            max_tokens=200,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        explanation = message.content[0].text.strip()

    except Exception as e:
        print(f"[explainability] Claude API call failed: {e}")
        # Fallback to basic explanation if API fails
        explanation = (
            f"Clause flagged as {risk_level} RISK.\n"
            f"Reason: {risk_reason}"
        )

    risk_analysis["explanation"] = explanation
    return risk_analysis
