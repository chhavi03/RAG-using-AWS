"""
run_ingestion.py
Full pipeline: list PDFs from S3 → extract pages → chunk → embed → store in OpenSearch.

Run once (or re-run to refresh):
  python run_ingestion.py
"""
from ingestion.load_data  import load_pdfs_from_s3
from ingestion.chunking   import chunk_pages
from ingestion.embed_store import store_chunk

print("=" * 60)
print("🚀  Starting RAG ingestion pipeline")
print("=" * 60)

# ── Step 1: Download & extract page-level text from S3 ──────────
print("\n📂  Step 1 — Loading PDFs from S3 …")
pages = load_pdfs_from_s3()
print(f"     Total pages extracted: {len(pages)}")

# ── Step 2: Chunk pages ─────────────────────────────────────────
print("\n✂️   Step 2 — Chunking pages …")
chunks = chunk_pages(pages, chunk_size=500, overlap=50)
print(f"     Total chunks produced: {len(chunks)}")

# ── Step 3: Embed & store ────────────────────────────────────────
print("\n🧠  Step 3 — Embedding & storing in OpenSearch …")
for i, chunk in enumerate(chunks):
    store_chunk(chunk)
    if (i + 1) % 25 == 0 or (i + 1) == len(chunks):
        pct = round((i + 1) / len(chunks) * 100)
        print(f"     [{pct:>3}%]  {i + 1}/{len(chunks)} chunks stored")

print("\n✅  Ingestion complete!\n")