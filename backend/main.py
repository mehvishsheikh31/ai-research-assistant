from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

app = FastAPI()

# Allow the HTML frontend (any origin) to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory vector store
vectorstore = None

# Fast local embeddings — no Ollama needed for this part.
# Downloads once (~90MB), then cached on disk.
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
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

        response = ollama.generate(model="tinyllama", prompt=prompt)
        answer = response.get("response", "No response generated.")
        return {"answer": answer}

    except Exception as e:
        print(f"[Chat Error] {e}")
        if "Connection refused" in str(e) or "ConnectError" in str(e):
            return {"answer": "Cannot reach Ollama. Make sure you ran 'ollama serve' and 'ollama pull tinyllama'."}
        return {"answer": f"Error: {str(e)}"}
