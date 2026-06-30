"""
app.py
Flask API for the AWS RAG system.

POST /query  →  { query: "..." }
             ←  { answer, sources: [{chunk_id, doc_name, doc_type, page, excerpt, url, score}] }

GET  /viewer            →  custom PDF viewer with text highlighting
GET  /document/<s3_key> →  redirects to a short-lived pre-signed S3 URL
"""
import os
import json
import urllib.parse
import re
from flask import Flask, request, jsonify, send_from_directory, redirect, Response, stream_with_context
from flask_cors import CORS

from utils.aws_clients       import get_bedrock_client, get_s3_client
from utils.opensearch_client import get_opensearch_client
from ingestion.embed_store   import get_embedding
from retrieval.retriever     import search_similar
from retrieval.prompt        import build_prompt
from config import S3_BUCKET, PRESIGNED_URL_EXPIRY, OPENSEARCH_INDEX

app               = Flask(__name__)
CORS(app)

bedrock           = get_bedrock_client()
s3_client         = get_s3_client()
opensearch_client = get_opensearch_client()

EXCERPT_LEN = 300   # characters to include in the "excerpt" field


# ── helpers ──────────────────────────────────────────────────────────────────

def _presigned_url(s3_key: str) -> str:
    """Generate a plain pre-signed S3 URL (no fragment) that expires in PRESIGNED_URL_EXPIRY seconds."""
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": s3_key},
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )


def _pick_highlight_phrase(text: str) -> str:
    """
    Pick the best 3–5 word phrase from the start of a chunk to use as
    the highlight search term in the PDF viewer.
    Favours longer, more distinctive words to improve matching accuracy.
    """
    words = re.findall(r'[a-zA-Z][a-zA-Z0-9]*', text)

    # Try to find a run of 4 words that are all reasonably long
    for window in (4, 3):
        for i in range(min(len(words) - window, 20)):          # check first 20 positions
            chunk = words[i:i + window]
            if all(len(w) >= 3 for w in chunk) and sum(len(w) for w in chunk) >= 15:
                return " ".join(chunk)

    # Fall back to first three words, whatever they are
    return " ".join(words[:3]) if words else ""


def _viewer_url(s3_key: str, page: int, highlight: str, excerpt: str, doc_name: str) -> str:
    """
    Build a URL pointing to our custom /viewer page.
    The viewer will fetch a fresh pre-signed URL from /api/presign and then
    render the PDF with the highlighted phrase.
    """
    params = {
        "s3_key":    s3_key,
        "page":      str(page),
        "highlight": highlight,
        "excerpt":   excerpt[:500],          # keep URL reasonable in length
        "name":      doc_name,
    }
    return "/viewer?" + urllib.parse.urlencode(params)


def _build_source_card(chunk: dict) -> dict:
    """Convert a retriever chunk dict into the API source card."""
    excerpt = chunk["text"][:EXCERPT_LEN]
    if len(chunk["text"]) > EXCERPT_LEN:
        excerpt += " …"

    highlight = _pick_highlight_phrase(chunk["text"])
    doc_name  = chunk["doc_name"]

    url = _viewer_url(
        s3_key    = chunk["s3_key"],
        page      = chunk["page"],
        highlight = highlight,
        excerpt   = excerpt,
        doc_name  = doc_name,
    )

    return {
        "chunk_id": chunk["chunk_id"],
        "doc_name": doc_name,
        "doc_type": chunk["doc_type"].upper(),
        "page":     chunk["page"],
        "s3_key":   chunk["s3_key"],
        "excerpt":  excerpt,
        "url":      url,
        "score":    chunk.get("score", 0),
    }


# ── routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return send_from_directory("../frontend", "code.html")


@app.route("/frontend/<path:filename>")
def frontend_assets(filename):
    return send_from_directory("../frontend", filename)


@app.route("/viewer")
def viewer():
    """
    Serve the custom PDF viewer (viewer.html).
    The viewer receives all params via URL query string; it calls /api/presign
    to exchange the s3_key for a fresh pre-signed URL at render time.
    """
    return send_from_directory("../frontend", "viewer.html")


@app.route("/api/pdf")
def api_pdf():
    """
    Stream the PDF from S3 through Flask so the browser never touches S3 directly.
    This sidesteps any S3 CORS restrictions entirely.

    GET /api/pdf?s3_key=data/my+doc.pdf
    """
    s3_key = request.args.get("s3_key", "").strip()
    if not s3_key:
        return jsonify({"error": "s3_key is required"}), 400

    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)

        def generate():
            for chunk in obj["Body"].iter_chunks(chunk_size=65536):
                yield chunk

        return Response(
            stream_with_context(generate()),
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{s3_key.split("/")[-1]}"',
                "Content-Length":      str(obj["ContentLength"]),
                "Cache-Control":       "private, max-age=300",
            },
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/document/<path:s3_key>")
def open_document(s3_key: str):
    """
    Legacy route — redirects directly to a raw pre-signed S3 URL.
    Use /viewer instead for the highlighted experience.
    """
    try:
        url = _presigned_url(s3_key)
        return redirect(url)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/query", methods=["POST"])
def query():
    payload    = request.get_json(silent=True) or {}
    user_query = (payload.get("query") or "").strip()

    if not user_query:
        return jsonify({"error": "Query is required."}), 400

    # ── 1. Embed the query ────────────────────────────────────────
    query_embedding = get_embedding(user_query)

    # ── 2. Retrieve top-k chunks with full metadata ───────────────
    chunks = search_similar(opensearch_client, query_embedding, k=5)

    if not chunks:
        return jsonify({
            "answer":  "I couldn't find any relevant information in the documents.",
            "sources": [],
        })

    # ── 3. Build prompt ───────────────────────────────────────────
    prompt = build_prompt(chunks, user_query)

    # ── 4. Call Amazon Nova Lite ──────────────────────────────────
    response = bedrock.invoke_model(
        modelId="amazon.nova-lite-v1:0",
        body=json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            "inferenceConfig": {
                "maxTokens": 512,
                "temperature": 0.3,
            },
        }),
    )
    result = json.loads(response["body"].read())
    raw_answer = result["output"]["message"]["content"][0]["text"]

    # ── 5. Parse follow-up questions out of the answer ────────────
    answer = raw_answer
    suggestions = []
    if "SUGGESTED_QUESTIONS:" in raw_answer:
        parts = raw_answer.split("SUGGESTED_QUESTIONS:")
        answer = parts[0].strip()
        suggestions_raw = parts[1].strip().split("\n")
        for line in suggestions_raw:
            clean = line.strip(" -*1234567890.[])")
            if clean:
                suggestions.append(clean)
        suggestions = suggestions[:3] # keep max 3

    # ── 6. Build source cards (with viewer URLs) ──────────────────
    sources = [_build_source_card(c) for c in chunks]

    return jsonify({
        "answer":      answer,
        "sources":     sources,
        "suggestions": suggestions,
    })


@app.route("/api/summarize", methods=["POST"])
def summarize_doc():
    payload = request.get_json(silent=True) or {}
    doc_name = (payload.get("doc_name") or "").strip()
    
    if not doc_name:
        return jsonify({"error": "doc_name required."}), 400

    cache_file = os.path.join(os.path.dirname(__file__), "summaries.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)
            if doc_name in cache:
                return jsonify(cache[doc_name])

    # Query OpenSearch for the first 10 chunks of this document
    query = {
        "size": 10,
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"doc_name": doc_name}},
                    {"range": {"page": {"lte": 10}}}
                ]
            }
        },
        "sort": [{"page": "asc"}]
    }
    
    opensearch_client = get_opensearch_client()
    try:
        response = opensearch_client.search(body=query, index=OPENSEARCH_INDEX)
        hits = response["hits"]["hits"]
    except Exception as e:
        return jsonify({"error": f"OpenSearch Error: {e}"}), 500

    if not hits:
        return jsonify({"error": "No data found for this document in the index."}), 404

    # combine text, limit to ~4500 chars 
    text_context = "\n".join([hit["_source"]["text"] for hit in hits])
    text_context = text_context[:4500]

    prompt = f"""You are a brilliant document summarizer. Give a highly informative 3-sentence summary of the following document excerpt. Then, provide exactly 5 important keyword tags that describe the topics covered.

Format your response exactly like this:
SUMMARY:
<your 3 sentences here>

TAGS:
- <tag1>
- <tag2>
- <tag3>
- <tag4>
- <tag5>

Document Excerpt:
{text_context}
"""

    try:
        res = bedrock.invoke_model(
            modelId="amazon.nova-lite-v1:0",
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"maxTokens": 300, "temperature": 0.3},
            }),
        )
        result = json.loads(res["body"].read())
        raw_answer = result["output"]["message"]["content"][0]["text"]
        
        summary = ""
        tags = []
        if "SUMMARY:" in raw_answer and "TAGS:" in raw_answer:
            parts = raw_answer.split("TAGS:")
            summary = parts[0].replace("SUMMARY:", "").strip()
            tags_raw = parts[1].strip().split("\n")
            tags = [t.strip(" -*") for t in tags_raw if t.strip(" -*")]
        else:
            summary = raw_answer.strip()

        final_result = {
            "summary": summary,
            "tags": tags[:5]
        }

        # save to cache
        cache = {}
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                try:
                    cache = json.load(f)
                except:
                    pass
        cache[doc_name] = final_result
        with open(cache_file, "w") as f:
            json.dump(cache, f, indent=2)

        return jsonify(final_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)