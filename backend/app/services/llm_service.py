from llama_index.llms.ollama import Ollama
from app.services.vector_service import vector_service

class LLMService:
      #call is great for research papers because 
        # it follows instructions well and is relatively fast.
        
    class LLMService:
     def __init__(self):
        # Change 'mistral' to 'tinyllama'
           self.llm = Ollama(
            model="tinyllama", 
            base_url="http://localhost:11434", 
            request_timeout=120.0
        )
 
     def ask_question(self, query_text: str):
        """
        The RAG Workflow:
        1. Fetch the index from FAISS.
        2. Use the Query Engine to search for the most relevant context.
        3. Send context + question to Mistral.
        """
        # Load the indexed vector data we created in Stage 7
        index = vector_service.get_index()
        
        if not index:
            return "No research papers found. Please upload a PDF first so I can learn from it!"

        # Create a Query Engine: This is the bridge.
        # similarity_top_k=3 finds the 3 most relevant paragraphs from your papers.
        query_engine = index.as_query_engine(
            llm=self.llm,
            similarity_top_k=3
        )

        # Generate the response
        response = query_engine.query(query_text)
        return response

# Instantiate the service
llm_service = LLMService()