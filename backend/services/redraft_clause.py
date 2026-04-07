"""
backend/services/redraft_clause.py

Uses Groq (llama-3.1-8b-instant) to suggest a safer redraft of a risky clause.
Called by the /api/redraft-clause endpoint.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path, encoding="utf-8")

try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment.")
        _client = Groq(api_key=api_key)
    return _client


def generate_redraft(
    clause_text: str,
    clause_type: str,
    risk_level: str,
    risk_reason: str,
    recommendations: list[str],
) -> str:
    """
    Given a risky clause and its risk metadata, return a safer rewritten version.

    Returns a plain string with the suggested redraft.
    Falls back to a rule-based template if Groq is unavailable.
    """
    if not _GROQ_AVAILABLE:
        return _fallback_redraft(clause_type, risk_reason, recommendations)

    recs_text = "\n".join(f"- {r}" for r in recommendations[:4]) if recommendations else "- No specific recommendations."

    prompt = f"""You are a senior legal counsel reviewing an NDA clause that has been flagged as {risk_level} risk.

CLAUSE TYPE: {clause_type}
RISK REASON: {risk_reason}

ORIGINAL CLAUSE:
\"\"\"{clause_text[:600]}\"\"\"

RECOMMENDED IMPROVEMENTS:
{recs_text}

Rewrite the clause to address the identified risks while preserving the original intent.
Rules:
1. Keep the same general purpose and structure
2. Fix the specific risk issues identified
3. Use clear, standard legal language
4. Do NOT add commentary or explanation — output ONLY the rewritten clause text
5. Keep it concise (similar length to original)

REWRITTEN CLAUSE:"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal drafting assistant. Output only the rewritten clause text, no explanations or headers.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.2,
        )
        redraft = response.choices[0].message.content.strip()

        # Strip common preamble phrases the model sometimes adds
        for prefix in ["REWRITTEN CLAUSE:", "Rewritten clause:", "Here is the rewritten clause:"]:
            if redraft.startswith(prefix):
                redraft = redraft[len(prefix):].strip()

        return redraft

    except Exception as e:
        print(f"[redraft_clause] Groq API failed: {e}")
        return _fallback_redraft(clause_type, risk_reason, recommendations)


def _fallback_redraft(clause_type: str, risk_reason: str, recommendations: list[str]) -> str:
    """Simple template fallback when Groq is unavailable."""
    recs = "\n".join(f"  • {r}" for r in recommendations[:3]) if recommendations else "  • Review and negotiate terms."
    return (
        f"[AI Redraft Suggestion — Groq unavailable]\n\n"
        f"This {clause_type} was flagged because: {risk_reason}\n\n"
        f"Suggested improvements to negotiate:\n{recs}\n\n"
        f"Please work with legal counsel to redraft this clause addressing the above points."
    )
