# 🧠 Grounded RAG System

> **Production-grade Retrieval-Augmented Generation (RAG) system with Hybrid Retrieval (FAISS + BM25), Citation Verification, FastAPI, Streamlit, Docker, and LLM-powered Question Answering.**

A modular, production-oriented Retrieval-Augmented Generation (RAG) platform that provides **grounded, citation-backed responses** over large document collections. The system combines semantic retrieval, keyword search, cross-encoder reranking, metadata filtering, and citation verification to reduce hallucinations and improve answer reliability.

Although the current implementation demonstrates the system using **clinical guidelines**, the architecture is **domain-independent** and can be adapted to legal documents, financial reports, enterprise knowledge bases, research papers, policy documents, and technical documentation.

---

# 🚀 Features

- Hybrid Retrieval (FAISS + BM25)
- HuggingFace Medical-Domain Embeddings
- CrossEncoder Re-ranking
- Metadata-aware Retrieval
- Citation Grounding & Verification
- FastAPI REST API
- Interactive Streamlit Interface
- SQLite Audit Logging
- Docker & Docker Compose Support
- Modular and Production-ready Architecture

---

# 📸 Demo

## Streamlit Dashboard

Replace these images with your screenshots.

### Home Page

```
images/home.png
```

![Home](images/home.png)

---

### Question Answering

```
images/query.png
```

![Question Answering](images/query.png)

---

### Retrieved Citations

```
images/results.png
```

![Results](images/results.png)

---

### Audit Trail

```
images/audit.png
```

![Audit](images/audit.png)

---

# 🏗️ System Architecture

```
                        User
                         │
                         ▼
                Streamlit Frontend
                         │
                         ▼
                  FastAPI Backend
                         │
        ┌────────────────────────────────┐
        │ Authentication + Rate Limiting │
        └────────────────────────────────┘
                         │
                         ▼
                Hybrid Retrieval Engine
             ┌──────────────┬──────────────┐
             │              │              │
             ▼              ▼              ▼
          FAISS          BM25        Metadata Filter
             └──────────────┬──────────────┘
                            ▼
                Reciprocal Rank Fusion
                            ▼
                 CrossEncoder Re-ranking
                            ▼
                   Grounded Prompt Builder
                            ▼
                       Large Language Model
                            ▼
                Citation Verification Engine
                            ▼
                     Structured JSON Response
                            ▼
                     SQLite Audit Logging
```

---

# ✨ Key Highlights

Unlike many demo RAG projects, this system includes several production-oriented features.

### Hybrid Retrieval

Combines

- Dense Retrieval (FAISS)
- Sparse Retrieval (BM25)

using Reciprocal Rank Fusion (RRF).

---

### CrossEncoder Re-ranking

Initial retrieval results are re-ranked using a CrossEncoder model to significantly improve retrieval quality.

---

### Metadata Filtering

Supports retrieval filtering using structured metadata such as

- Source Organization
- Document Type
- Category
- Version
- Section
- Page Number

---

### Citation Verification

Every generated citation is validated against the retrieved document metadata before being returned.

This provides an additional safeguard against hallucinated references.

---

### Audit Trail

Every query records

- User Question
- Retrieved Documents
- Citations
- Grounding Score
- Latency
- Timestamp

for traceability and debugging.

---

# 🛠️ Technology Stack

| Category | Technologies |
|-----------|--------------|
| Language | Python |
| Backend | FastAPI |
| Frontend | Streamlit |
| Vector Database | FAISS |
| Keyword Retrieval | BM25 |
| Embeddings | HuggingFace Sentence Transformers |
| Re-ranking | CrossEncoder |
| LLM | Groq / OpenAI / Anthropic / Gemini / OpenRouter |
| Database | SQLite |
| Containerization | Docker |
| Deployment | Docker Compose |

---

# 📂 Project Structure

```
grounded-rag-system/

├── app/
│   ├── core/
│   ├── middleware/
│   ├── routers/
│   ├── config.py
│   ├── dependencies.py
│   └── main.py
│
├── ingestion/
│
├── scripts/
│
├── streamlit_app/
│
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/grounded-rag-system.git

cd grounded-rag-system
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create

```
.env
```

Example

```env
LLM_PROVIDER=groq

GROQ_API_KEY=YOUR_KEY

LLM_MODEL=llama-3.3-70b-versatile

EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

TOP_K=5

SCORE_THRESHOLD=0.35
```

---

# 📄 Add Documents

Place PDFs inside

```
data/raw_guidelines/
```

Then build the vector index.

```bash
python -m ingestion.build_index
```

---

# ▶️ Run Backend

```bash
uvicorn app.main:app --reload
```

API Documentation

```
http://localhost:8000/docs
```

---

# ▶️ Run Streamlit

```bash
streamlit run streamlit_app/app.py
```

Open

```
http://localhost:8501
```

---

# 🐳 Docker

Build and run

```bash
docker compose up --build
```

---

# 🔍 Example Query

```
What are the WHO recommendations for hypertension treatment?
```

---

# 📈 API Response

```json
{
  "answer": "...",
  "citations": [
    {
      "source_org": "WHO",
      "page": 18,
      "section": "Treatment Recommendations"
    }
  ],
  "grounding_verified": true,
  "grounding_score": 1.0,
  "latency_ms": 842
}
```

---

# 🧪 Running Tests

```bash
pytest tests/ -v
```

---

# 🔮 Future Improvements

- Multi-Query Retrieval
- Context Compression
- Adaptive Top-K Retrieval
- Redis Rate Limiting
- PostgreSQL Audit Database
- OAuth2 Authentication
- Retrieval Evaluation Dashboard
- Kubernetes Deployment
- CI/CD Pipeline
- Multi-modal Document Support

---

# ⚠️ Disclaimer

This project demonstrates **citation-grounded Retrieval-Augmented Generation** for document question answering.

It is intended for research and educational purposes. Any domain-specific outputs (such as healthcare guidance) should always be reviewed by qualified professionals before being used for decision-making.

---

# 👩‍💻 Author

**Shruti Agarwal**

M.Tech
Indian Institute of Technology Kharagpur

GitHub: [https://github.com/Avisha2803]

LinkedIn: https://www.linkedin.com/in/shruti2803/
