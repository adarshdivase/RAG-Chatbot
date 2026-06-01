# Aura Enterprise RAG — 60-Second Demo Script

Use this flow when presenting to recruiters, interviewers, or on a portfolio walkthrough.

## Before you start

```powershell
# From Projects folder — one command (Windows)
.\RAG-Chatbot\scripts\start-demo.ps1
```

Or manually: backend on `:8000`, frontend on `:5500`, open http://127.0.0.1:5500/?api=http://127.0.0.1:8000

Ensure `backend/.env` has a valid `GOOGLE_API_KEY`.

---

## Minute 0:00 — Hook (10 sec)

> "This is **Aura Enterprise** — a RAG assistant over a curated MLOps knowledge base. Answers are grounded in documents with citations, not hallucinated freely."

Point to: sidebar stats (documents, chunks), status **Connected**.

---

## Minute 0:10 — Ask a strong question (20 sec)

Click a **suggested question** chip, e.g.:

- *"What are best practices for scalable ML model deployment?"*

Show:

1. Answer in the chat
2. Expand **sources** — file names + snippets
3. Latency / model in the message footer

---

## Minute 0:30 — Follow-up (15 sec)

Ask a follow-up **without repeating context**:

> *"How does that relate to Kubernetes?"*

Shows **history-aware retrieval** (reformulates the question using chat context).

---

## Minute 0:45 — Knowledge base ops (15 sec)

1. Click **Upload document** (or mention existing files in sidebar)
2. Optional: **Reindex knowledge base** — mention chunks count updates
3. **Export chat** — download the conversation as Markdown

---

## Five questions that work well

These map to files in `data/`:

| # | Question |
|---|----------|
| 1 | What is explainable AI (XAI) and why does it matter? |
| 2 | Compare cloud MLOps platforms on AWS, Azure, and GCP. |
| 3 | What are best practices for scalable ML model deployment? |
| 4 | What ethical considerations apply to generative AI? |
| 5 | How does Kubernetes support cloud-native MLOps? |

---

## Troubleshooting live

| Issue | Fix |
|-------|-----|
| Status **Offline** | Start backend; check API URL in sidebar |
| **Indexing…** banner | Wait 30–60s on first boot (Chroma + embeddings) |
| 401 error | Remove API key in sidebar unless `API_KEY` is set in `.env` |
| Weak answers | Click **Reindex**; confirm documents listed in sidebar |

---

## Closing line (5 sec)

> "Stack: FastAPI, Gemini, ChromaDB, session-aware RAG with MMR retrieval — full source on GitHub."
