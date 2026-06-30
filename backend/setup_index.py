"""
setup_index.py
Deletes existing index and creates a fresh one with updated mappings.

Run ONCE before first ingestion, or to fully reset:
  python setup_index.py
"""
import warnings
warnings.filterwarnings("ignore")   # suppress InsecureRequestWarning

from utils.opensearch_client import get_opensearch_client
from config import OPENSEARCH_INDEX, EMBED_DIMENSIONS

client     = get_opensearch_client()
index_name = OPENSEARCH_INDEX

# ── Delete existing index ─────────────────────────────────────────────────────
if client.indices.exists(index=index_name):
    client.indices.delete(index=index_name)
    print(f"🗑️   Deleted existing index '{index_name}' (all embeddings wiped)")
else:
    print(f"ℹ️   No existing index '{index_name}' found — creating fresh")

# ── Index settings & mappings ─────────────────────────────────────────────────
# Using engine=faiss (nmslib is deprecated in OpenSearch 3.x)
index_body = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 512,
        }
    },
    "mappings": {
        "properties": {
            # ── Vector field (Titan v2 = 1024 dims by default) ────────────────
            "embedding": {
                "type":      "knn_vector",
                "dimension": EMBED_DIMENSIONS,
                "method": {
                    "name":       "hnsw",
                    "space_type": "l2",
                    "engine":     "faiss",          # nmslib removed in OpenSearch 3.x
                    "parameters": {
                        "ef_construction": 512,
                        "m":               16,
                    },
                },
            },
            # ── Chunk metadata ────────────────────────────────────────────────
            "chunk_id": {"type": "keyword"},
            "s3_key":   {"type": "keyword"},
            "doc_name": {
                "type": "text",
                "fields": {"raw": {"type": "keyword"}},
            },
            "doc_type": {"type": "keyword"},
            "page":     {"type": "integer"},
            "text":     {"type": "text"},
        }
    },
}

client.indices.create(index=index_name, body=index_body)
print(f"✅  Index '{index_name}' created")
print(f"     Engine    : faiss  (hnsw)")
print(f"     Dimensions: {EMBED_DIMENSIONS}")
print(f"     Model     : amazon.titan-embed-text-v2:0")
print(f"\n👉  Now run:  python run_ingestion.py")