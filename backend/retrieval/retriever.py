"""
retriever.py
Performs a k-NN vector search in OpenSearch and returns full chunk metadata dicts.
"""
from config import OPENSEARCH_INDEX


def search_similar(
    opensearch_client,
    query_embedding: list[float],
    k: int = 5,
) -> list[dict]:
    """
    Returns a list of source dicts, each containing:
      chunk_id, s3_key, doc_name, doc_type, page, text
    """
    query = {
        "size": k,
        "_source": ["chunk_id", "s3_key", "doc_name", "doc_type", "page", "text"],
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": k,
                }
            }
        },
    }

    response = opensearch_client.search(index=OPENSEARCH_INDEX, body=query)

    results = []
    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        results.append({
            "chunk_id": src.get("chunk_id", hit["_id"]),
            "s3_key":   src.get("s3_key", ""),
            "doc_name": src.get("doc_name", "Unknown"),
            "doc_type": src.get("doc_type", "pdf").upper(),
            "page":     src.get("page", 0),
            "text":     src.get("text", ""),
            "score":    round(hit.get("_score", 0), 4),
        })

    return results
