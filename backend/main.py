"""
AI Research Assistant - backend
Fixes vs original:
  - Blocking work (embeddings, FAISS search, Ollama generate) moved off the
    event loop via run_in_executor, so the server stays responsive while
    TinyLlama is thinking.
  - Multiple papers supported at once, each with its own FAISS index.
  - Indexes persisted to disk (VECTOR_STORE_PATH) and reloaded on startup,
    so a restart no longer loses everything.
  - Chat answers include which paper + page(s) the context came from.
  - Uploaded files are written with tempfile (no filename collisions) and
    are size/type-guarded before processing.
"""

import os
import re
import shutil
import tempfile
import asyncio
from functools import partial
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

OLLAMA_BASE_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME        = os.getenv("MODEL_NAME", "tinyllama")
EMBED_MODEL_NAME  = os.getenv("EMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
VECTOR_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", ".")) / "vector_store"
MAX_UPLOAD_MB     = int(os.getenv("MAX_UPLOAD_MB", "25"))

VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

# paper_id -> {"name": str, "store": FAISS}
papers: dict[str, dict] = {}
active_paper_id: str | None = None

ollama_client = ollama.Client(host=OLLAMA_BASE_URL)


class ChatRequest(BaseModel):
    query: str
    paper_id: str | None = None  # if omitted, uses the active paper


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_")
    return slug or "paper"


def _run_blocking(fn, *args, **kwargs):
    """Run a blocking call in a background thread so the event loop is free."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, partial(fn, *args, **kwargs))


def _load_existing_indexes():
    """Reload any FAISS indexes saved to disk from a previous run."""
    global active_paper_id
    if not VECTOR_STORE_PATH.exists():
        return
    for entry in VECTOR_STORE_PATH.iterdir():
        if not entry.is_dir():
            continue
        try:
            store = FAISS.load_local(
                str(entry), embeddings, allow_dangerous_deserialization=True
            )
            name_file = entry / "display_name.txt"
            display_name = name_file.read_text().strip() if name_file.exists() else entry.name
            papers[entry.name] = {"name": display_name, "store": store}
        except Exception as e:
            print(f"[Startup] Failed to load index '{entry.name}': {e}")
    if papers and active_paper_id is None:
        active_paper_id = next(iter(papers))


@app.on_event("startup")
async def on_startup():
    await _run_blocking(_load_existing_indexes)


@app.get("/")
async def root():
    return {"status": "online", "message": "AI Research Assistant API is ready"}


@app.get("/status")
async def status():
    return {
        "backend": "online",
        "paper_loaded": active_paper_id is not None,
        "active_paper_id": active_paper_id,
        "papers": [{"id": pid, "name": p["name"]} for pid, p in papers.items()],
    }


@app.post("/select")
async def select_paper(paper_id: str):
    global active_paper_id
    if paper_id not in papers:
        raise HTTPException(status_code=404, detail="Unknown paper_id.")
    active_paper_id = paper_id
    return {"active_paper_id": active_paper_id}


@app.delete("/paper/{paper_id}")
async def delete_paper(paper_id: str):
    global active_paper_id
    if paper_id not in papers:
        raise HTTPException(status_code=404, detail="Unknown paper_id.")
    del papers[paper_id]
    shutil.rmtree(VECTOR_STORE_PATH / paper_id, ignore_errors=True)
    if active_paper_id == paper_id:
        active_paper_id = next(iter(papers), None)
    return {"deleted": paper_id, "active_paper_id": active_paper_id}


def _index_pdf(file_path: str, display_name: str, paper_id: str):
    """Blocking: load PDF, split, embed, build + persist FAISS index."""
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    if not pages:
        raise ValueError("PDF is empty or unreadable.")

    for doc in pages:
        doc.metadata["source"] = display_name

    store = FAISS.from_documents(pages, embeddings)

    dest = VECTOR_STORE_PATH / paper_id
    dest.mkdir(parents=True, exist_ok=True)
    store.save_local(str(dest))
    (dest / "display_name.txt").write_text(display_name)

    return store, len(pages)


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global active_paper_id

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    paper_id = _slugify(Path(file.filename).stem)
    suffix = ".pdf"
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)

    try:
        size = 0
        limit = MAX_UPLOAD_MB * 1024 * 1024
        with os.fdopen(tmp_fd, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds {MAX_UPLOAD_MB} MB limit.",
                    )
                buffer.write(chunk)

        store, num_pages = await _run_blocking(
            _index_pdf, tmp_path, file.filename, paper_id
        )

        papers[paper_id] = {"name": file.filename, "store": store}
        active_paper_id = paper_id

        return {
            "message": f"Successfully indexed: {file.filename} ({num_pages} pages)",
            "paper_id": paper_id,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[Upload Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _search(store: FAISS, query: str, k: int = 4):
    return store.similarity_search(query, k=k)


def _generate(prompt: str):
    response = ollama_client.generate(model=MODEL_NAME, prompt=prompt)
    return response.get("response", "No response generated.")


@app.post("/chat")
async def chat(request: ChatRequest):
    paper_id = request.paper_id or active_paper_id

    if not request.query.strip():
        return {"answer": "Please type a question."}

    if paper_id is None or paper_id not in papers:
        return {"answer": "No paper loaded yet. Please upload a PDF first."}

    store = papers[paper_id]["store"]

    try:
        docs = await _run_blocking(_search, store, request.query, 4)

        context_parts = []
        sources = []
        for doc in docs:
            page = doc.metadata.get("page")
            page_label = f"p.{page + 1}" if isinstance(page, int) else "p.?"
            context_parts.append(f"[{page_label}] {doc.page_content}")
            sources.append({"paper": papers[paper_id]["name"], "page": page_label})

        context = "\n\n".join(context_parts)

        prompt = f"""You are a helpful research assistant. Answer the question based ONLY on the provided context from the research paper. Be concise and clear. If the context does not contain the answer, say so.

Context from paper:
{context}

Question: {request.query}

Answer:"""

        answer = await _run_blocking(_generate, prompt)

        return {
            "answer": answer,
            "sources": sources,
            "paper_id": paper_id,
            "paper_name": papers[paper_id]["name"],
        }

    except Exception as e:
        print(f"[Chat Error] {e}")
        if "Connection refused" in str(e) or "ConnectError" in str(e):
            return {
                "answer": f"Cannot reach Ollama at {OLLAMA_BASE_URL}. "
                          f"Make sure 'ollama serve' is running."
            }
        return {"answer": f"Error: {str(e)}"}