from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.pdf_processor import processor
from app.services.vector_service import vector_service # New import
import uvicorn

app = FastAPI(title="AI Research Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs allowed")

    try:
        # 1. Save and Load PDF
        path = await processor.save_file(file)
        documents = processor.load_pdf(path)
        
        # 2. Index the document (Create Embeddings and store in FAISS)
        # This makes the paper "searchable" by the AI
        index = vector_service.create_index(documents)
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks_indexed": "Index updated successfully"
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ready"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)