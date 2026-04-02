import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import re
import os


# -----------------------------
# Lazy-load summarizer globally
# -----------------------------
summarizer = None

def get_summarizer():
    """
    Load the Hugging Face summarization model only once.
    Returns None if it fails and logs the error.
    """
    global summarizer
    if summarizer is None:
        try:
            print("[INFO] Loading AI summarization model...")
            # Explicitly load tokenizer + model for better error logging
            model_name = "sshleifer/distilbart-cnn-12-6"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            summarizer = pipeline("text2text-generation", model=model, tokenizer=tokenizer)
            print("[SUCCESS] Model loaded successfully!")
        except Exception as e:
            print("[ERROR] AI model loading failed:", e)
            summarizer = None
    return summarizer


# -----------------------------
# Rule-based fallback summarizer
# -----------------------------
def simple_summary(text: str, max_sentences: int = 3) -> str:
    """
    Simple keyword-based summarization fallback.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    # Start with first 2 sentences
    summary = sentences[:2]

    # Keyword scoring
    keywords = ["agreement", "shall", "party", "law", "confidential"]
    scored = [(sum(1 for kw in keywords if kw in sent.lower()), sent) for sent in sentences]
    scored.sort(reverse=True)

    for _, sent in scored[:max_sentences]:
        if sent not in summary:
            summary.append(sent)

    return " ".join(summary[:max_sentences])


# -----------------------------
# Chunk text for transformer
# -----------------------------
def chunk_text(text: str, max_chunk_size: int = 1000) -> list:
    """
    Split long documents into chunks to avoid transformer max length errors.
    """
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


# -----------------------------
# Run summarization
# -----------------------------
def run_summarization(text: str, max_length=130, min_length=30) -> dict:
    """
    Run AI summarizer if possible. Fallback only if AI fails.
    Returns a dict with 'final_summary' and 'pipeline'.
    """
    if not text.strip():
        return {
            "final_summary": "",
            "pipeline": "No text provided"
        }

    chunks = chunk_text(text, max_chunk_size=1000)
    summarizer_model = get_summarizer()
    summaries = []
    ai_succeeded = False

    if summarizer_model:
        print("[INFO] Running AI summarization...")
        for idx, chunk in enumerate(chunks):
            if len(chunk.strip()) < 20:
                continue
            try:
                result = summarizer_model(chunk, max_length=60, min_length=20, do_sample=False)
                
                if isinstance(result, list) and len(result) > 0:
                    if 'summary_text' in result[0]:
                        summaries.append(result[0]['summary_text'])
                    elif 'generated_text' in result[0]:  # <-- add this
                        summaries.append(result[0]['generated_text'])
                    elif isinstance(result[0], str):
                        summaries.append(result[0])
                else:
                    print(f"Unexpected summarizer output: {result[0]}")
                ai_succeeded = True

            except Exception as e:
                print(f"[ERROR] Failed to summarize chunk {idx}: {e}")

        if ai_succeeded:
            print("[INFO] AI summarization succeeded!")

    final_summary = "\n\n".join(summaries).strip() 

    # If AI failed for all chunks, use fallback
    if not final_summary:
        print("[INFO] AI summarization failed,Now using fallback...")
        final_summary = simple_summary(text)
        pipeline_used = "Rule-based Summarization"
    else:
        pipeline_used = "AI Summarization"

    return {
        "final_summary": final_summary,
        "pipeline": pipeline_used,
        "key_facts": "Key facts extraction pending (To Do)",
        "doc_length": len(text)
    }