import logging
from langchain_community.document_loaders import PyPDFLoader

class Reader:
    """
    Uses Langchain PyPDFLoader to extract elements from a PDF.
    """
    def __init__(self):
        self.logger = logging.getLogger("worker.ingest.reader")

    def extract_elements(self, file_path: str):
        """
        Converts the PDF into a list of Langchain Document objects.
        """
        self.logger.info(f"Extracting elements from {file_path} using Langchain PyPDFLoader...")
        
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        return documents
