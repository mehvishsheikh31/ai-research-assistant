import os
import faiss
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter

class VectorService:
    def __init__(self, storage_dir: str = "data/faiss_index"):
        self.storage_dir = storage_dir
        
        # 1. Define the Embedding Model (Local, no API key needed)
        # This turns text into 384-dimensional vectors
        self.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # 2. Define the Chunking Strategy
        self.node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)

    def create_index(self, documents):
        """
        Takes documents, chunks them, creates embeddings, and saves to FAISS.
        """
        # Create a FAISS index
        # 384 is the dimension size of our MiniLM model
        d = 384 
        faiss_index = faiss.IndexFlatL2(d)
        
        # Initialize the vector store
        vector_store = FaissVectorStore(faiss_index=faiss_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Build the index from documents
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context,
            embed_model=self.embed_model,
            transformations=[self.node_parser]
        )
        
        # Save the index to the data/faiss_index folder
        index.storage_context.persist(persist_dir=self.storage_dir)
        return index

    def get_index(self):
        """
        Loads the existing index from disk.
        """
        if os.path.exists(os.path.join(self.storage_dir, "default__vector_store.json")):
            # Rebuild storage context
            vector_store = FaissVectorStore.from_persist_dir(self.storage_dir)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store, persist_dir=self.storage_dir
            )
            # Load index
            return load_index_from_storage(storage_context, embed_model=self.embed_model)
        return None

# Initialize the service
vector_service = VectorService()