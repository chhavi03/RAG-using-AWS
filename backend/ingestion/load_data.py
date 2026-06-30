"""
load_data.py
Downloads every PDF in S3_BUCKET/S3_PREFIX and extracts text page-by-page.

Returns a list of page dicts:
  {
    "s3_key":   "data/deep learning.pdf",
    "doc_name": "deep learning",
    "doc_type": "pdf",
    "page":     1,          # 1-indexed
    "text":     "..."
  }
"""
import io
from PyPDF2 import PdfReader
from utils.aws_clients import get_s3_client
from config import S3_BUCKET, S3_PREFIX


def _extract_doc_name(s3_key: str) -> str:
    """Strip the prefix and extension to get a human-readable doc name."""
    filename = s3_key.split("/")[-1]            # e.g. "deep learning.pdf"
    name, _ = filename.rsplit(".", 1)           # e.g. "deep learning"
    return name


def load_pdfs_from_s3() -> list[dict]:
    """List all .pdf objects under S3_PREFIX and extract page-level text."""
    s3 = get_s3_client()
    pages = []

    # List objects in the bucket under the given prefix
    paginator = s3.get_paginator("list_objects_v2")
    for page_result in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX):
        for obj in page_result.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(".pdf"):
                continue

            print(f"  📥  Downloading s3://{S3_BUCKET}/{key} …")
            response = s3.get_object(Bucket=S3_BUCKET, Key=key)
            pdf_bytes = response["Body"].read()

            doc_name = _extract_doc_name(key)
            reader   = PdfReader(io.BytesIO(pdf_bytes))

            for page_idx, pdf_page in enumerate(reader.pages):
                text = pdf_page.extract_text() or ""
                text = text.strip()
                if not text:
                    continue        # skip blank pages

                pages.append({
                    "s3_key":   key,
                    "doc_name": doc_name,
                    "doc_type": "pdf",
                    "page":     page_idx + 1,   # 1-indexed
                    "text":     text,
                })

            print(f"     ✅  {doc_name}  →  {len(reader.pages)} pages")

    return pages
