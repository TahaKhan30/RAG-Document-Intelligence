"""PDF text extraction using PyMuPDF. Returns per-page text so we can track page numbers for citations."""
import fitz  # PyMuPDF
from fastapi import HTTPException


def extract_pages(pdf_bytes: bytes) -> list[dict]:
    """
    Extract text page by page.
    Returns list of {page_number, text}.
    Page numbers are 1-indexed for human-friendly citations.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open PDF: {e}")

    pages = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append({"page_number": i + 1, "text": text})

    doc.close()

    if not pages:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found. The PDF may be scanned or image-based."
        )

    return pages


def count_words(pages: list[dict]) -> int:
    return sum(len(p["text"].split()) for p in pages)
