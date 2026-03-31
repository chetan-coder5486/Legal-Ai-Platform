"""
summarizer.py  -  Legal Contract Summarizer
=============================================
Usage:
    from summarizer import run_summarization, summarize_by_label, analyze_contract
"""

import re
from transformers import pipeline

# ── Model config ───────────────────────────────────────────────────────────────
MODEL_NAME     = "sshleifer/distilbart-cnn-12-6"
MAX_CHUNK_SIZE = 1500
SUMMARY_MAX    = 130
SUMMARY_MIN    = 30

# ── Lazy model loader ──────────────────────────────────────────────────────────
_summarizer = None

def _get_model():
    global _summarizer
    if _summarizer is None:
        print("Loading summarization model...")
        _summarizer = pipeline(
            "summarization",
            model=MODEL_NAME,
            truncation=True,
        )
        print("Model ready.")
    return _summarizer


# ── Text utilities ─────────────────────────────────────────────────────────────
def _clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


def chunk_text(text: str, max_chunk_size: int = MAX_CHUNK_SIZE) -> list:
    lines = text.split("\n")
    chunks, current, current_len = [], [], 0

    for line in lines:
        if current_len + len(line) > max_chunk_size:
            if current:
                chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += len(line) + 1

    if current:
        chunks.append("\n".join(current))

    return chunks


# ── Core summarization ─────────────────────────────────────────────────────────
def _summarize_chunks(chunks: list) -> list:
    model = _get_model()
    summaries = []

    for idx, chunk in enumerate(chunks):
        if len(chunk.strip()) < 50:
            continue
        try:
            input_length = len(chunk.split())
            dynamic_max  = min(SUMMARY_MAX, max(30, input_length // 2))
            dynamic_min  = min(SUMMARY_MIN, dynamic_max - 5)

            out = model(
                chunk,
                max_length=dynamic_max,
                min_length=dynamic_min,
                do_sample=False,
            )
            summaries.append(out[0]["summary_text"])
        except Exception as exc:
            print(f"[summarizer] Warning - chunk {idx} failed: {exc}")

    return summaries


def run_summarization(text: str) -> dict:
    """
    Full contract summarization pipeline.
    Returns a dict with status, final_summary, key_facts, doc_length, chunk_count.
    """
    if not text or not text.strip():
        return {"status": "error", "message": "Empty text provided."}

    cleaned   = _clean_text(text)
    chunks    = chunk_text(cleaned)
    summaries = _summarize_chunks(chunks)

    if not summaries:
        return {"status": "error", "message": "Could not generate any summary."}

    merged = " ".join(summaries)
    if len(summaries) > 1 and len(merged) > 200:
        second_pass   = _summarize_chunks([merged])
        final_summary = second_pass[0] if second_pass else merged
    else:
        final_summary = merged

    return {
        "pipeline":      "Summarization",
        "status":        "ok",
        "final_summary": final_summary,
        "key_facts":     _extract_key_facts(cleaned),
        "doc_length":    len(text),
        "chunk_count":   len(chunks),
    }


# ── Per-label summarization ────────────────────────────────────────────────────
def summarize_by_label(labeled_clauses: dict) -> dict:
    """
    Summarize each clause label separately.
    Input:  { "Payment": ["clause1", "clause2"], "Termination": ["clause3"] }
    Output: { "Payment": {"summary": "...", "clause_count": 2}, ... }
    """
    if not labeled_clauses:
        return {}

    results = {}
    for label, clauses in labeled_clauses.items():
        if not clauses:
            continue
        combined       = " ".join(clauses)
        summary_result = run_summarization(combined)
        results[label] = {
            "summary":      summary_result.get("final_summary", ""),
            "clause_count": len(clauses),
            "status":       summary_result.get("status", "error"),
        }

    return results


# ── Key facts extraction ───────────────────────────────────────────────────────
def _extract_key_facts(text: str) -> dict:
    facts = {}

    date_patterns = [
        r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b",
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]
    dates = []
    for pat in date_patterns:
        dates.extend(re.findall(pat, text, flags=re.IGNORECASE))
    if dates:
        facts["dates_found"] = list(dict.fromkeys(dates))[:10]

    amounts = re.findall(
        r"(?:USD?|Rs\.?|INR|€|£|\$)\s?[\d,]+(?:\.\d{2})?",
        text,
        flags=re.IGNORECASE,
    )
    if amounts:
        facts["amounts_found"] = list(dict.fromkeys(amounts))[:10]

    party_match = re.search(
        r"between\s+(.+?)\s+(?:hereinafter|,?\s*\"|\(|\band\b)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if party_match:
        facts["first_party"] = party_match.group(1).strip()[:120]

    duration = re.findall(
        r"(?:for\s+a\s+period\s+of|term\s+of|duration\s+of)\s+[\d\w\s]+(?:year|month|day)s?",
        text,
        flags=re.IGNORECASE,
    )
    if duration:
        facts["duration"] = duration[0].strip()[:120]

    return facts if facts else {"note": "No structured facts auto-extracted."}


# ── Full pipeline wrapper ──────────────────────────────────────────────────────
def analyze_contract(contract_text: str, labeled_clauses: dict = None) -> dict:
    """
    One-call wrapper: summarize full contract + each label category.

    Args:
        contract_text:   raw contract string
        labeled_clauses: { "Termination": [...], "Payment": [...] }  (optional)

    Returns combined report dict.
    """
    report = run_summarization(contract_text)

    if labeled_clauses:
        report["label_summaries"] = summarize_by_label(labeled_clauses)

    report["pipeline"] = "Legal AI - Full Analysis"
    return report
