from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class RecursiveSplitter:
    """
    Uses LangChain's RecursiveCharacterTextSplitter to chunk the cleaned text.
    """
    def __init__(self, chunk_size=800, chunk_overlap=150):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
        )

    def split(self, cleaned_data, source_file: str):
        """
        Converts the dict data into LangChain Documents and splits them.
        """
        documents = []
        
        for section in cleaned_data:
            doc = Document(
                page_content=section["content"],
                metadata={
                    "source": source_file,
                    "page": section["page"]
                }
            )
            documents.append(doc)
            
        return self.splitter.split_documents(documents)