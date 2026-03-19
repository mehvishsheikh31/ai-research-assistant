from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
import ollama
import os
import shutil

app = FastAPI()

# This is your "Global Memory"
vectorstore = None 

class ChatRequest(BaseModel):
    query: str

@app.get("/")
async def root():
    return {"status": "online", "message": "Research Assistant API is ready"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global vectorstore
    try:
        # 1. Save the file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Load and Split the PDF
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()

        # 3. Create the Vector Store (The "Memory")
        embeddings = OllamaEmbeddings(model="tinyllama")
        vectorstore = FAISS.from_documents(pages, embeddings)

        # 4. Clean up the temp file
        os.remove(file_path)
        
        return {"message": f"Successfully indexed {file.filename}"}
    except Exception as e:
        print(f"Upload Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    global vectorstore
    try:
        if vectorstore is None:
            return {"answer": "Please upload a PDF paper first!"}

        # 1. Search the PDF for context
        docs = vectorstore.similarity_search(request.query, k=3)
        context = "\n".join([doc.page_content for doc in docs])

        # 2. Ask the AI (TinyLlama)
        prompt = f"Using this context: {context}\n\nQuestion: {request.query}"
        response = ollama.generate(model="tinyllama", prompt=prompt)

        return {"answer": response['response']}
    except Exception as e:
        print(f"Chat Error: {str(e)}")
        return {"answer": f"I had an error: {str(e)}"}