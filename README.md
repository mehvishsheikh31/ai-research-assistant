# AI Research Assistant 🤖📄

A locally-hosted RAG (Retrieval-Augmented Generation) system.
Upload any research PDF and chat with it privately.
**No data leaves your machine.**

---

## 📁 Project Structure

```
ai-research-assistant/
│
├── backend/
│   ├── __init__.py
│   └── main.py
│
├── frontend/
│   └── index.html
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

* **Backend:** FastAPI + Uvicorn
* **AI Model:** Ollama (TinyLlama) — runs fully locally
* **Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (HuggingFace)
* **Vector Search:** FAISS
* **PDF Loading:** LangChain + PyPDF
* **Frontend:** Plain HTML + CSS + JavaScript (no framework)

---

## ⚙️ Setup

### 1️⃣ Prerequisites

* Python 3.10+
* [Ollama](https://ollama.com/) installed

---

### 2️⃣ Install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

---

### 3️⃣ Pull the AI model (one-time)

```bash
ollama pull tinyllama
```

---

### 4️⃣ Configure `.env`

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=tinyllama
EMBED_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
PAPER_DIR=.
VECTOR_STORE_PATH=.
```

---

## 🚀 Running the App

### Terminal 1 — Ollama

*(Skip if already running)*

```bash
ollama serve
```

---

### Terminal 2 — Backend

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8888 --reload
```

---

### Open Frontend

Open:

```
frontend/index.html
```

No extra server needed.

---

## 🧠 Usage

1. Wait for **"Backend online"** status (green)
2. Click the upload area and select a PDF
3. Click **Upload & Index Paper** and wait for confirmation
4. Type your question and press Enter
5. Wait ~1–2 minutes for TinyLlama to respond
   *(CPU is slow — this is normal)*

---

## 📝 Notes

* Paper is stored in memory only — re-upload after restarting the backend
* First run downloads the embedding model (~90MB), cached after that
* Ollama only needs to be started once

  * If port `11434` is already in use, it's already running

---
