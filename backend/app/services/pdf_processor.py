import os
import shutil
from fastapi import UploadFile
from llama_index.core import SimpleDirectoryReader

class PDFProcessor:
    def __init__(self, upload_dir: str = "data/papers"):
        self.upload_dir = upload_dir
        # Create the directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    async def save_file(self, file: UploadFile) -> str:
        """Saves the uploaded file to the disk."""
        file_path = os.path.join(self.upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    def load_pdf(self, file_path: str):
        """Loads the PDF and converts it into LlamaIndex Document objects."""
        # SimpleDirectoryReader is the easiest way to load specific files
        reader = SimpleDirectoryReader(input_files=[file_path])
        documents = reader.load_data()
        return documents

# Create a single instance to be used across the app
processor = PDFProcessor()