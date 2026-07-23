import logging
from unstructured.partition.pdf import partition_pdf

class Reader:
    """
    Uses Unstructured to extract raw elements and structure from a PDF.
    """
    def __init__(self):
        self.logger = logging.getLogger("worker.ingest.reader")

    def extract_elements(self, file_path: str):
        """
        Converts the PDF into a list of unstructured elements.
        """
        self.logger.info(f"Extracting elements from {file_path} using Unstructured...")
        

        elements = partition_pdf(filename=file_path)
        
        return elements
