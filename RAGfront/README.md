# 🌌 Aura: Your Intelligent Knowledge Assistant

**Aura** is a fully functional, document-grounded chatbot powered by Retrieval-Augmented Generation (RAG), integrating:
- 🔮 **Gemini Pro** (Google Generative AI)
- 🧠 **LangChain**
- 🗂️ **ChromaDB** as the vector store
- 🚀 **FastAPI** backend
- 🎨 **TailwindCSS** frontend

Aura allows users to query documents, get answers with cited sources, and re-index the knowledge base—all through an intuitive interface.

---

## 📦 Features

- ✅ Conversational AI with memory and context
- 📂 Upload and ingest `.txt`, `.pdf`, `.docx`, and `.csv` documents
- 🔁 One-click knowledge base re-indexing
- 🔗 Source attribution with metadata on hover
- 🧪 Health-check endpoint for backend monitoring
- 🔧 Fully Dockerized backend
- 🖼️ Sleek, mobile-responsive Tailwind frontend
- 📋 "Copy" button for responses

---

## 🏗️ Project Structure

```
aura_chatbot/
├── backend/
│   ├── main.py              # FastAPI app with RAG pipeline
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Secure your Gemini API key here
├── frontend/
│   └── index.html           # UI with TailwindCSS and real-time chat
├── data/
│   ├── knowledge_files.txt  # Add your knowledge base documents here
├── Dockerfile               # Docker deployment config
└── README.md                # You're reading this!
```

---

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/aura-chatbot.git
cd aura-chatbot
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Add Your `.env`

```
GOOGLE_API_KEY=your_gemini_pro_api_key
```

### 4. Run Backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🖥️ Frontend Setup

You can simply open:

```
frontend/index.html
```

Or deploy the frontend to Vercel/Netlify and **update the `BACKEND_URL`** in the JavaScript.

---

## 🐳 Docker Deployment

```bash
docker build -t aura-chatbot .
docker run -p 8000:8000 aura-chatbot
```

---

## 🔌 API Endpoints

| Method | Endpoint        | Description                          |
|--------|-----------------|--------------------------------------|
| GET    | `/health`       | Backend health status                |
| POST   | `/chat`         | Submit a message and get AI reply    |
| POST   | `/reindex_kb`   | Re-ingest all documents in `/data`   |
| POST   | `/upload_document` | Upload document dynamically        |

---

## 🧠 Powered By

- 🟨 [LangChain](https://github.com/langchain-ai/langchain)
- 🟢 [Gemini Pro](https://ai.google.dev/)
- 🟣 [ChromaDB](https://www.trychroma.com/)
- 🔵 [FastAPI](https://fastapi.tiangolo.com/)
- 🟡 [TailwindCSS](https://tailwindcss.com/)
- 🐋 Docker

---

## 👤 Author

**Aayush Yadav**  
🌐 [Portfolio](https://aayush-yadav-portfolio.vercel.app)  
💻 [GitHub](https://github.com/03ADY)

---

## 📄 License

Open-source for educational and demonstration purposes.
