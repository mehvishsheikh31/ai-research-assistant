from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, shutil
from dotenv import load_dotenv
import ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Load .env from project root
load_dotenv()

OLLAMA_BASE_URL  = os.getenv("OLLAMA_BASE_URL",  "http://localhost:11434")
MODEL_NAME       = os.getenv("MODEL_NAME",        "tinyllama")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME",  "sentence-transformers/all-MiniLM-L6-v2")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

vectorstore = None

embeddings = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


class ChatRequest(BaseModel):
    query: str


@app.get("/")
async def root():
    return {"status": "online", "message": "AI Research Assistant API is ready"}


@app.get("/status")
async def status():
    return {"backend": "online", "paper_loaded": vectorstore is not None}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global vectorstore
    file_path = f"temp_{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()

        if not pages:
            raise HTTPException(status_code=400, detail="PDF is empty or unreadable.")

        vectorstore = FAISS.from_documents(pages, embeddings)
        return {"message": f"Successfully indexed: {file.filename} ({len(pages)} pages)"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Upload Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/chat")
async def chat(request: ChatRequest):
    global vectorstore
    try:
        if vectorstore is None:
            return {"answer": "No paper loaded yet. Please upload a PDF first."}

        if not request.query.strip():
            return {"answer": "Please type a question."}

        docs = vectorstore.similarity_search(request.query, k=4)
        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = f"""You are a helpful research assistant. Answer the question based ONLY on the provided context from the research paper. Be concise and clear.

Context from paper:
{context}

Question: {request.query}

Answer:"""

        client = ollama.Client(host=OLLAMA_BASE_URL)
        response = client.generate(model=MODEL_NAME, prompt=prompt)
        answer = response.get("response", "No response generated.")
        return {"answer": answer}

    except Exception as e:
        print(f"[Chat Error] {e}")
        if "Connection refused" in str(e) or "ConnectError" in str(e):
            return {"answer": f"Cannot reach Ollama at {OLLAMA_BASE_URL}. Make sure 'ollama serve' is running."}
        return {"answer": f"Error: {str(e)}"}