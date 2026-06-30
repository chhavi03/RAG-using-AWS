AWS_REGION = "us-east-1"       # Bedrock region
S3_REGION  = "ap-south-1"      # S3 bucket region  ← change if different

S3_BUCKET = "rag-bot-jatin-001"
S3_PREFIX = "data/"            # folder in S3 where PDFs are stored

OPENSEARCH_HOST  = "search-rag-opensearch-fk3z7zosbdmhznnoauhhyeskay.aos.ap-south-1.on.aws"
OPENSEARCH_INDEX = "rag-index"

# ── Embedding: Titan Text Embeddings v2 (1024-dim, faster & better than v1) ──
BEDROCK_EMBED_MODEL = "amazon.titan-embed-text-v2:0"
EMBED_DIMENSIONS     = 1024        # v2 default; also supports 256 / 512

BEDROCK_LLM_MODEL   = "amazon.nova-lite-v1:0"

PRESIGNED_URL_EXPIRY = 3600   # seconds (1 hour)
