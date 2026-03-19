
---

# AI Research Assistant 🤖📄

A locally hosted **Retrieval-Augmented Generation (RAG)** system built to help researchers and students interact with their PDF papers using private AI. No data leaves your machine.

## 🚀 Features (Current Version)
* **Local PDF Indexing:** Uses `PyPDFLoader` and `FAISS` to turn research papers into searchable vector data.
* **Private AI Chat:** Powered by `Ollama` (TinyLlama) for fast, local inference on your laptop.
* **Modern UI:** A dark-mode dashboard built with `Reflex` for seamless interaction.
* **FastAPI Logic:** A high-performance backend managing the bridge between PDF data and the AI model.

---

## 🏗️ Project Architecture
```text
ai-research-assistant/
├── backend/            # FastAPI Server (Logic & AI Bridge)
│   └── main.py         # Main API routes (Upload & Chat)
├── frontend/           # Reflex UI (The Dashboard)
│   └── research_app/   # Frontend source code
├── data/               # Vector storage (FAISS) and Paper uploads
└── requirements.txt    # Project dependencies
```

---

## 🛠️ Tech Stack
* **Frontend:** [Reflex](https://reflex.dev/) (Python-based Web Framework)
* **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
* **AI Engine:** [Ollama](https://ollama.com/) (Model: `tinyllama`)
* **Orchestration:** [LangChain](https://www.langchain.com/)
* **Vector Database:** [FAISS](https://github.com/facebookresearch/faiss)

---

## 🚦 Getting Started

### 1. Prerequisites
* Python 3.10+
* [Ollama](https://ollama.com/) installed and running (`ollama pull tinyllama`)

### 2. Installation
```bash
# Clone the repo
git clone https://github.com/mehvishsheikh31/ai-research-assistant.git
cd ai-research-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the System
You need **three** terminals open:

* **Terminal 1 (Ollama):** `ollama serve`
* **Terminal 2 (Backend):** ```bash
    cd backend
    python -m uvicorn main:app --host 127.0.0.1 --port 8888
    ```
* **Terminal 3 (Frontend):** ```bash
    cd frontend/research_app
    reflex run
    ```

---

## 📝 Usage
1. Open your browser to `http://localhost:3000`.
2. Upload a research paper (PDF format) via the sidebar.
3. Wait for the "Paper Indexed" alert.
4. Ask questions about the paper in the chat box!

---

## 🛠️ Troubleshooting (Device Guard Policy)
If running on a restricted Windows machine, always start the backend using the `python -m` bypass:
`python -m uvicorn main:app --host 127.0.0.1 --port 8888`

---

## 📅 Roadmap
* [ ] Add support for multiple PDF comparison.
* [ ] Implement persistent storage for FAISS indexes.
* [ ] Enhance UI with "Thinking" animations and chat history.

---

---
