import io
import re
import shutil
from pathlib import Path
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

# ─── Optional OCR (only needed for scanned PDFs) ───────────────────────────

try:
    import pytesseract
except ImportError:
    pytesseract = None
tesseract_path = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if pytesseract is not None:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

try:
    from PIL import Image
    OCR_AVAILABLE = bool(
        pytesseract is not None
        and fitz is not None
        and (shutil.which("tesseract") or Path(tesseract_path).exists())
    )
except ImportError:
    OCR_AVAILABLE = False


# ─── PDF extraction ────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Multi-strategy PDF text extraction with structure preservation.

    Strategy order:
      1. PyMuPDF with layout-aware 'blocks' extraction (fast, preserves structure)
      2. pdfplumber (more accurate for complex layouts / tables)
      3. pytesseract OCR (for scanned / image-only PDFs)
    """
    text = _extract_with_pymupdf(file_bytes)

    # If PyMuPDF yields too little text, the PDF is likely scanned or badly encoded
    if len(text.strip()) < 100:
        text = _extract_with_pdfplumber(file_bytes)

    # Final fallback: OCR page-by-page
    if len(text.strip()) < 100:
        text = _extract_with_ocr(file_bytes)

    return text


def _extract_with_pymupdf(file_bytes: bytes) -> str:
    """
    Extract text using PyMuPDF in natural reading order.
    Much better for legal documents than block-based extraction.
    """
    pages_text = []
    if fitz is None:
        return ""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            text = page.get_text("text")  # 🔥 KEY FIX
            if text.strip():
                pages_text.append(text.strip())
    except Exception as e:
        print(f"[parsers] PyMuPDF failed: {e}")

    return "\n\n".join(pages_text)


def _extract_with_pdfplumber(file_bytes: bytes) -> str:
    """
    Accurate extraction for complex layouts using pdfplumber.
    Falls back gracefully if a page fails.
    """
    pages_text = []
    if pdfplumber is None:
        return ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text(x_tolerance=3, y_tolerance=3)
                if extracted:
                    pages_text.append(extracted.strip())
    except Exception as e:
        print(f"[parsers] pdfplumber failed: {e}")
    return "\n\n".join(pages_text)


def _extract_with_ocr(file_bytes: bytes) -> str:
    """
    OCR fallback for scanned / image-only PDFs using pytesseract.
    Renders each page as a high-resolution image before OCR.
    Requires: pip install pytesseract pillow
    """
    if not OCR_AVAILABLE:
        print("[parsers] OCR unavailable — install pytesseract and Pillow.")
        return ""

    pages_text = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            # Render at 2x resolution for better OCR accuracy
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = pytesseract.image_to_string(img, config="--psm 6")
            if ocr_text.strip():
                pages_text.append(ocr_text.strip())
    except Exception as e:
        print(f"[parsers] OCR failed: {e}")
    return "\n\n".join(pages_text)


# ─── DOCX extraction ───────────────────────────────────────────────────────

def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from Word documents, preserving paragraph structure.
    Skips empty paragraphs to avoid blank-line noise.
    """
    if docx is None:
        raise ValueError("DOCX support is unavailable because python-docx is not installed.")
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


# ─── Text cleaning ─────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 🔥 CRITICAL: join broken sentences
    text = re.sub(r"\n(?=[a-z])", " ", text)

    # 🔥 fix broken uppercase headings
    text = re.sub(r"([A-Z])\n([A-Z])", r"\1 \2", text)

    # preserve paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)

    # spacing cleanup
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)

    # remove page artifacts
    text = re.sub(r"(?i)(page\s+\d+\s+of\s+\d+|\-\s*\d+\s*\-)", "", text)

    return text.strip()


# ─── Main entry point ──────────────────────────────────────────────────────

def parse_document(filename: str, file_bytes: bytes) -> str:
    """
    Route the uploaded file to the correct extractor, then clean the result.
    Returns a structured string with paragraph breaks intact.
    Raises ValueError for unsupported formats.
    """
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext in ("doc", "docx"):
        raw_text = extract_text_from_docx(file_bytes)
    elif ext == "txt":
        raw_text = file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file format: .{ext}")

    cleaned = clean_text(raw_text)

    if not cleaned:
        raise ValueError(
            "No text could be extracted from this document. "
            "It may be a scanned image PDF without OCR support."
        )

    return cleaned
