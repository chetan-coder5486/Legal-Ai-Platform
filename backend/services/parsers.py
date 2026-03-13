import pdfplumber
import fitz  # PyMuPDF
import docx
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using PyMuPDF (fast) or pdfplumber (accurate)."""
    text = ""
    try:
        # Try PyMuPDF first for speed
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
    except Exception as e:
        print(f"PyMuPDF failed: {e}. Falling back to pdfplumber.")
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as fallback_e:
             print(f"pdfplumber failed: {fallback_e}")
    
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a Word document."""
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def clean_text(text: str) -> str:
    """Basic text cleaning."""
    # Remove excessive whitespace
    text = " ".join(text.split())
    return text

def parse_document(filename: str, file_bytes: bytes) -> str:
    """Main entry point for parsing uploaded documents."""
    ext = filename.split(".")[-1].lower()
    
    if ext == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext in ["doc", "docx"]:
        raw_text = extract_text_from_docx(file_bytes)
    elif ext == "txt":
        raw_text = file_bytes.decode("utf-8")
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    
    return clean_text(raw_text)
