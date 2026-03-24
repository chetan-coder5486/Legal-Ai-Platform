from transformers import pipeline
import textwrap

# Lazy-load to prevent slow startup time unless necessary
# We'll use a fast model for summs. 
summarizer = None

def get_summarizer():
    global summarizer
    if summarizer is None:
        # Using a fast summarization model for prototyping
        # In production use facebook/bart-large-cnn or specialized legal model
        print("Loading summarization model...")
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    return summarizer

def chunk_text(text: str, max_chunk_size: int = 2000) -> list:
    \"\"\"Split long document text into chunks appropriate for transformer input size.\"\"\"
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
            current_length += len(line) + 1  # +1 for newline
            
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks

def run_summarization(text: str) -> dict:
    \"\"\"
    Run the Summarizer pipeline.
    Text Cleaning -> Chunk -> Summarize -> Merge
    \"\"\"
    if not text.strip():
        return {"error": "Empty text provided."}
        
    chunks = chunk_text(text, max_chunk_size=1500)
    summarizer_model = get_summarizer()
    
    summaries = []
    for idx, chunk in enumerate(chunks):
        if len(chunk.strip()) > 50: # Skip very short snippets that can't be summarized
            try:
                out = summarizer_model(chunk, max_length=130, min_length=30, do_sample=False)
                summaries.append(out[0]['summary_text'])
            except Exception as e:
                print(f"Error summarising chunk {idx}: {e}")
                
    final_summary = "\n\n".join(summaries)
    
    return {
        "pipeline": "Summarization",
        "final_summary": final_summary,
        "key_facts": "Auto-extraction of key facts requires secondary NLP pass (To Do).",
        "doc_length": len(text)
    }
