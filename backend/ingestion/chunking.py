"""
chunking.py
Splits page-level text into overlapping chunks while preserving all source metadata.

Each chunk dict:
  {
    "chunk_id": "uuid4-string",
    "s3_key":   "data/deep learning.pdf",
    "doc_name": "deep learning",
    "doc_type": "pdf",
    "page":     3,
    "text":     "..."
  }
"""
import uuid


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    Takes the list of page dicts returned by load_pdfs_from_s3() and
    splits each page's text into overlapping fixed-size chunks.
    """
    chunks = []

    for page in pages:
        text = page["text"]
        step = max(chunk_size - overlap, 1)

        for start in range(0, len(text), step):
            chunk_text = text[start : start + chunk_size].strip()
            if not chunk_text:
                continue

            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "s3_key":   page["s3_key"],
                "doc_name": page["doc_name"],
                "doc_type": page["doc_type"],
                "page":     page["page"],
                "text":     chunk_text,
            })

    return chunks
