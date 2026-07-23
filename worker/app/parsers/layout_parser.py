class LayoutParser:
    """
    Groups extracted elements into sections and pages.
    """
    def group_elements(self, elements):
        """
        Iterates over the Langchain Documents and groups text by page number.
        Returns a list of dictionaries with 'page' and 'content'.
        """
        pages_data = {}
        
        # Extract text items and group them by page
        for item in elements:
            metadata = getattr(item, "metadata", {})
            # Langchain documents typically store page in metadata (0-indexed)
            page_no = metadata.get("page", 0) + 1
            
            if page_no not in pages_data:
                pages_data[page_no] = []
            
            content = getattr(item, "page_content", "")
            if content:
                pages_data[page_no].append(str(content))
        
        # Format into a structured list of sections
        structured_data = []
        for page_no, texts in pages_data.items():
            structured_data.append({
                "page": page_no,
                "content": "\n".join(texts)
            })
            
        return structured_data