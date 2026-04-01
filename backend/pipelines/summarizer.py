import textwrap
import re

try:
    from transformers import pipeline as hf_pipeline
    _TRANSFORMERS_IMPORT_ERROR = None
except Exception as e:
    hf_pipeline = None
    _TRANSFORMERS_IMPORT_ERROR = e

# Lazy-load to prevent slow startup time unless necessary
summarizer = None

def get_summarizer():
    global summarizer
    if summarizer is None:
        if hf_pipeline is None:
            print(f"Model loading failed: transformers unavailable ({_TRANSFORMERS_IMPORT_ERROR})")
            return None
        try:
            print("Loading summarization model...")
            summarizer = hf_pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        except Exception as e:
            print("Model loading failed:", e)
            summarizer = None
    return summarizer


# -------------------------------
# 🔥 FALLBACK FUNCTION (ADDED)
# -------------------------------
def simple_summary(text: str, max_sentences: int = 5) -> str:
    sentences = re.split(r'(?<=[.!?]) +', text)

    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    summary = sentences[:2]

    keywords = ["agreement", "shall", "party", "law", "confidential"]

    scored = []
    for sent in sentences:
        score = sum(1 for word in keywords if word in sent.lower())
        scored.append((score, sent))

    scored.sort(reverse=True)

    for _, sent in scored[:max_sentences]:
        if sent not in summary:
            summary.append(sent)

    return " ".join(summary[:5])


def chunk_text(text: str, max_chunk_size: int = 2000) -> list:
    """Split long document text into chunks appropriate for transformer input size."""
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_length = 0
    
    for line in lines:
        if current_length + len(line) > max_chunk_size:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = len(line)
        else:
            current_chunk.append(line)
            current_length += len(line) + 1
            
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks


def run_summarization(text: str) -> dict:
    """
    Run the Summarizer pipeline.
    Text Cleaning -> Chunk -> Summarize -> Merge
    """
    if not text.strip():
        return {"error": "Empty text provided."}
        
    chunks = chunk_text(text, max_chunk_size=1500)
    summarizer_model = get_summarizer()
    
    summaries = []

    # 🔹 Try AI summarization if model loaded
    if summarizer_model:
        for idx, chunk in enumerate(chunks):
            if len(chunk.strip()) > 50:
                try:
                    out = summarizer_model(
                        chunk,
                        max_length=100,
                        min_length=30,
                        do_sample=False
                    )
                    summaries.append(out[0]['summary_text'])
                except Exception as e:
                    print(f"Error summarising chunk {idx}: {e}")

    final_summary = "\n\n".join(summaries)
    # 🔥 Compress final summary again
    if summarizer_model and len(final_summary) > 200:
        try:
            compressed = summarizer_model(
                final_summary,
                max_length=180,
                min_length=30,
                do_sample=False
            )
            final_summary = compressed[0]['summary_text']
        except:
            pass

    # 🔥 FALLBACK TRIGGER #
    if not final_summary.strip():
        print("Using fallback summarizer...")
        final_summary = simple_summary(text)
        pipeline_used = "Rule-based Summarization"
    else:
        pipeline_used = "AI Summarization"

    return {
        "pipeline": pipeline_used,
        "final_summary": final_summary,
        "key_facts": "Auto-extraction of key facts requires secondary NLP pass (To Do).",
        "doc_length": len(text)
    }
