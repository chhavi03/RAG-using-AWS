# AWS RAG Assistant

A document intelligence chatbot powered by **AWS Bedrock**, **OpenSearch**, and **S3**.  
Ask questions across multiple PDFs and get answers with exact page numbers, document names, and clickable source links.

---

## Project Structure

```
aws rag/
├── backend/                    # Python Flask API
│   ├── app.py                  # Main server — /query, /document routes
│   ├── config.py               # All configuration (S3 bucket, regions, models)
│   ├── requirements.txt        # Python dependencies
│   ├── run_ingestion.py        # Run once to ingest PDFs from S3
│   ├── setup_index.py          # Run once to create the OpenSearch index
│   │
│   ├── ingestion/              # Data pipeline
│   │   ├── load_data.py        # Downloads PDFs from S3, extracts page-level text
│   │   ├── chunking.py         # Splits pages into chunks with UUID + metadata
│   │   └── embed_store.py      # Embeds chunks and stores in OpenSearch
│   │
│   ├── retrieval/              # RAG query pipeline
│   │   ├── retriever.py        # k-NN vector search in OpenSearch
│   │   └── prompt.py           # Builds LLM prompt from retrieved chunks
│   │
│   └── utils/                  # AWS client helpers
│       ├── aws_clients.py      # Bedrock + S3 boto3 clients
│       └── opensearch_client.py
│
├── frontend/                   # UI
│   └── code.html               # Single-page chat interface
│
└── data/                       # Local copies of PDFs (upload these to S3)
```

---

## Setup & Run

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Upload PDFs to S3
```bash
aws s3 cp ../data/ s3://rag-bot-jatin-001/data/ --recursive
```

### 3. Create OpenSearch index (one-time)
```bash
python setup_index.py
```

### 4. Ingest documents (one-time, or when PDFs change)
```bash
python run_ingestion.py
```

### 5. Start the server
```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## How it works

1. **Ingestion** — PDFs are downloaded from S3, split into 500-char chunks (with page metadata + UUID), embedded via Amazon Titan, and indexed in OpenSearch.
2. **Query** — User question is embedded, top-5 matching chunks are retrieved from OpenSearch, passed to Amazon Nova Lite for an answer.
3. **Response** — Returns the answer + source cards with document name, page number, UUID, excerpt, and a pre-signed S3 URL to open the exact page.

---

## Tech Stack

| Layer | Service |
|---|---|
| LLM | Amazon Nova Lite (Bedrock) |
| Embeddings | Amazon Titan Embed Text v1 |
| Vector DB | Amazon OpenSearch Service |
| Storage | Amazon S3 |
| Backend | Python · Flask |
| Frontend | HTML · Tailwind CSS |

---

## System Workflows

### 1. Document Ingestion Workflow (Batch Processing)

This offline pipeline processes raw PDFs and indexes them into the vector database.

```mermaid
flowchart TD
    classDef startEnd fill:#ffffff,stroke:#333333,stroke-width:2px;
    classDef process fill:#ffffff,stroke:#475569,stroke-width:2px;
    classDef aiModel fill:#e6f9f9,stroke:#0d9488,stroke-width:2px;
    classDef decision fill:#ffffff,stroke:#2563eb,stroke-width:2px;
    classDef errorBlock fill:#fef2f2,stroke:#ef4444,stroke-width:2px;
    classDef successBlock fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;
    classDef pendingBlock fill:#fffbeb,stroke:#f59e0b,stroke-width:2px;

    Start[/PDF Documents in data/ folder/]:::startEnd
    Upload[Upload PDFs to S3 Bucket<br>aws s3 cp]:::process
    Trigger[Run Ingestion Script<br>run_ingestion.py]:::process
    Download[Download & Extract Page Text<br>PyPDF2 & boto3 in load_data.py]:::process
    CheckText{Is Page Text Extracted?}:::decision
    
    Skip[Skip Blank/Scanned Page<br>No Text Layer]:::errorBlock
    Chunk[Split into 500-char Overlapping Chunks<br>chunking.py]:::pendingBlock
    Embed[Generate Embeddings<br>amazon.titan-embed-text-v2:0]:::aiModel
    Store[Index Chunks & Metadata in OpenSearch<br>opensearch-py on rag-index]:::successBlock

    Start --> Upload
    Upload --> Trigger
    Trigger --> Download
    Download --> CheckText
    
    CheckText -- No --> Skip
    CheckText -- Yes --> Chunk
    Chunk --> Embed
    Embed --> Store
```

### 2. Query Retrieval & PDF Streaming Workflow (Real-Time)

This online pipeline handles user questions, executes semantic searches, generates answers, and streams highlighted sources.

```mermaid
flowchart TD
    classDef startEnd fill:#ffffff,stroke:#333333,stroke-width:2px;
    classDef process fill:#ffffff,stroke:#475569,stroke-width:2px;
    classDef aiModel fill:#e6f9f9,stroke:#0d9488,stroke-width:2px;
    classDef decision fill:#ffffff,stroke:#2563eb,stroke-width:2px;
    classDef errorBlock fill:#fef2f2,stroke:#ef4444,stroke-width:2px;
    classDef successBlock fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;
    classDef pendingBlock fill:#fffbeb,stroke:#f59e0b,stroke-width:2px;

    Query[/User Query entered in Chat UI<br>code.html/]:::startEnd
    Send[POST Request to Flask API /query<br>app.py]:::process
    Vectorize[Generate Query Embedding<br>amazon.titan-embed-text-v2:0]:::aiModel
    OSQuery[k-NN Similarity Vector Search<br>opensearch-py on rag-index]:::process
    CheckResult{Are Relevant Chunks Found?}:::decision

    NoResult[Return 'No info found' response<br>Status 200 with empty sources]:::errorBlock
    BuildPrompt[Construct Prompt with Context Chunks<br>prompt.py]:::process
    LLMGenerate[Generate Answer & Suggestions<br>amazon.nova-lite-v1:0 via Bedrock]:::aiModel
    PrepCards[Build Source Cards with Viewer URLs<br>_build_source_card in app.py]:::pendingBlock
    RenderUI[Display Chat Answer & Source Cards<br>code.html]:::process
    ClickSource[User clicks Source Card]:::process
    StreamPDF[Stream PDF chunks securely through Flask<br>/api/pdf via boto3 from S3]:::successBlock
    ShowPDF[/Render exact PDF page & highlight phrase<br>viewer.html using PDF.js/]:::startEnd

    Query --> Send
    Send --> Vectorize
    Vectorize --> OSQuery
    OSQuery --> CheckResult

    CheckResult -- No --> NoResult
    CheckResult -- Yes --> BuildPrompt
    BuildPrompt --> LLMGenerate
    LLMGenerate --> PrepCards
    PrepCards --> RenderUI
    RenderUI --> ClickSource
    ClickSource --> StreamPDF
    StreamPDF --> ShowPDF
```

### 3. Document Summarizer Workflow (Optional/On-demand)

This pipeline provides document-level summaries and dynamic tags on demand.

```mermaid
flowchart TD
    classDef startEnd fill:#ffffff,stroke:#333333,stroke-width:2px;
    classDef process fill:#ffffff,stroke:#475569,stroke-width:2px;
    classDef aiModel fill:#e6f9f9,stroke:#0d9488,stroke-width:2px;
    classDef decision fill:#ffffff,stroke:#2563eb,stroke-width:2px;
    classDef errorBlock fill:#fef2f2,stroke:#ef4444,stroke-width:2px;
    classDef successBlock fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;
    classDef pendingBlock fill:#fffbeb,stroke:#f59e0b,stroke-width:2px;

    SummReq[/Request Summary for Doc/]:::startEnd
    CheckCache{Summary Cached in summaries.json?}:::decision
    ReturnCache[Read Summary & Tags from Local Cache]:::successBlock
    OSSearch[Query OpenSearch for first 10 pages<br>Sort by page ascending]:::process
    LLMSummarize[Generate 3-Sentence Summary & 5 Tags<br>amazon.nova-lite-v1:0 via Bedrock]:::aiModel
    WriteCache[Save to summaries.json cache]:::pendingBlock

    SummReq --> CheckCache
    CheckCache -- Yes --> ReturnCache
    CheckCache -- No --> OSSearch
    OSSearch --> LLMSummarize
    LLMSummarize --> WriteCache
    WriteCache --> ReturnCache
```
