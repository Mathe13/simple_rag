class LayoutParser:
    """
    Groups extracted elements into sections and pages.
    """
    def group_elements(self, docling_document):
        """
        Iterates over the docling document and groups text by page number.
        Returns a list of dictionaries with 'page' and 'content'.
        """
        pages_data = {}
        
        # Extract text items and group them by page
        for item in docling_document.texts:
            # Docling stores provenance (prov) which contains page numbers
            page_no = item.prov[0].page_no if item.prov else 1
            
            if page_no not in pages_data:
                pages_data[page_no] = []
            pages_data[page_no].append(item.text)
        
        # Format into a structured list of sections
        structured_data = []
        for page_no, texts in pages_data.items():
            structured_data.append({
                "page": page_no,
                "content": "\n".join(texts)
            })
            
        return structured_data