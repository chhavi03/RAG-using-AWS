"""
embed_store.py
Generates a Bedrock embedding for a text chunk and indexes the full metadata
document into OpenSearch.

Uses: amazon.titan-embed-text-v2:0  (1024 dimensions, higher quality than v1)

OpenSearch document schema:
  {
    "chunk_id":  "uuid4",
    "s3_key":    "data/deep learning.pdf",
    "doc_name":  "deep learning",
    "doc_type":  "pdf",
    "page":      3,
    "text":      "...",
    "embedding": [...]       # 1024-dim float vector
  }
"""
import json
import warnings
warnings.filterwarnings("ignore")

from utils.aws_clients import get_bedrock_client
from utils.opensearch_client import get_opensearch_client
from config import BEDROCK_EMBED_MODEL, OPENSEARCH_INDEX, EMBED_DIMENSIONS

bedrock           = get_bedrock_client()
opensearch_client = get_opensearch_client()


def get_embedding(text: str) -> list[float]:
    """
    Call Amazon Titan Text Embeddings v2 and return the embedding vector.
    v2 accepts:  inputText, dimensions (int), normalize (bool)
    """
    response = bedrock.invoke_model(
        modelId=BEDROCK_EMBED_MODEL,
        body=json.dumps({
            "inputText":  text,
            "dimensions": EMBED_DIMENSIONS,   # 1024 (default), 512, or 256
            "normalize":  True,               # unit-normalize for cosine similarity
        }),
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def store_chunk(chunk: dict) -> None:
    """
    Embed chunk["text"] via Titan v2 and index the full chunk metadata
    into OpenSearch. chunk_id is used as the document _id (idempotent upsert).
    """
    embedding = get_embedding(chunk["text"])

    doc = {
        "chunk_id": chunk["chunk_id"],
        "s3_key":   chunk["s3_key"],
        "doc_name": chunk["doc_name"],
        "doc_type": chunk["doc_type"],
        "page":     chunk["page"],
        "text":     chunk["text"],
        "embedding": embedding,
    }

    opensearch_client.index(
        index=OPENSEARCH_INDEX,
        id=chunk["chunk_id"],   # chunk UUID → idempotent re-ingestion
        body=doc,
    )