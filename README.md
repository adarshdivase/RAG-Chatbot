# Aura Enterprise RAG Platform

Production-grade **Retrieval-Augmented Generation** stack: modular FastAPI backend, Gemini LLM, ChromaDB vector store, session-aware chat, document management, and an enterprise web UI.

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────────┐
│  Web UI         │────▶│  FastAPI  /api/v1                          │
│  (Frontend)     │     │  ├── Chat (history-aware RAG)              │
└─────────────────┘     │  ├── Documents (upload / list / delete)    │
                        │  ├── Sessions (per-user memory)            │
                        │  └── System (health / ready / metrics)     │
                        └──────────────┬─────────────────────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │  ChromaDB  +  Gemini 2.0   │
                        │  MMR retrieval · citations   │
                        └─────────────────────────────┘
```

## Features

| Capability | Description |
|------------|-------------|
| **History-aware RAG** | Reformulates follow-up questions using chat context |
| **MMR retrieval** | Diverse, relevant chunks (reduces redundant answers) |
| **Session isolation** | Per-session memory with TTL and eviction |
| **Document API** | Upload, list, delete, full reindex |
| **Security** | Optional `X-API-Key`, rate limiting, request IDs |
| **Observability** | `/health`, `/ready`, `/live`, `/metrics`, structured logs |
| **Docker** | Multi-stage ready `Dockerfile` + `docker-compose` |

## Demo preview

![Aura Enterprise RAG UI](docs/demo-preview.svg)

## One-command demo (recommended)

**Windows** (from `Projects` folder):

```powershell
.\RAG-Chatbot\scripts\start-demo.ps1
```

**macOS / Linux**:

```bash
chmod +x RAG-Chatbot/scripts/start-demo.sh
./RAG-Chatbot/scripts/start-demo.sh
```

This starts the API (`:8000`), UI (`:5500`), and opens the browser. See **[DEMO.md](DEMO.md)** for a 60-second presenter script.

### Docker (API + UI)

```bash
cd RAG-Chatbot
# Set GOOGLE_API_KEY in backend/.env first
docker compose up --build
```

- API: http://127.0.0.1:8000/docs  
- UI: http://127.0.0.1:5500/?api=http://127.0.0.1:8000  

## Manual start

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set GOOGLE_API_KEY
uvicorn main:app --reload --port 8000
```

### Frontend (separate repo)

```bash
cd ../RAG-Chatbot-Frontend/frontend
python -m http.server 5500
```

Open: http://127.0.0.1:5500/?api=http://127.0.0.1:8000

## API reference (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat` | Ask a question |
| `GET` | `/api/v1/documents` | List indexed files |
| `POST` | `/api/v1/documents/upload` | Upload & reindex |
| `DELETE` | `/api/v1/documents/{name}` | Delete & reindex |
| `POST` | `/api/v1/documents/reindex` | Full reindex |
| `DELETE` | `/api/v1/sessions/{id}` | Clear session memory |
| `GET` | `/ready` | Readiness probe |
| `GET` | `/metrics` | Usage metrics |

Legacy routes `/chat` and `/reindex_kb` remain for backward compatibility.

## Configuration

See `backend/.env.example`. Key variables:

- `GOOGLE_API_KEY` — required
- `API_KEY` — optional; enforces `X-API-Key` on all v1 routes
- `GEMINI_MODEL` — default `gemini-2.0-flash`
- `DATA_DIR` — knowledge base folder (default `../data`)
- `CHROMA_DIR` — vector store persistence

## Project layout

```
RAG-Chatbot/
├── backend/
│   ├── app/
│   │   ├── api/v1/       # REST routers
│   │   ├── core/         # security, logging, middleware
│   │   ├── ingestion/    # loaders + Chroma pipeline
│   │   ├── models/       # Pydantic schemas
│   │   └── services/     # RAG engine + sessions
│   ├── main.py           # Uvicorn entry
│   ├── storage/chroma/   # persisted embeddings (gitignored)
│   └── tests/
├── data/                 # knowledge base documents
├── Dockerfile
└── docker-compose.yml
```

## Security notes

- Never commit `.env` or API keys.
- Set `API_KEY` in production and pass it from the UI or gateway.
- Tune `RATE_LIMIT_PER_MINUTE` and `CORS_ORIGINS` for your deployment.

## License

See repository license file.
