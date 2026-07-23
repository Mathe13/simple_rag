class LayoutParser:
    """
    Groups extracted elements into sections and pages.
    """
    def group_elements(self, elements):
        """
        Iterates over the unstructured elements and groups text by page number.
        Returns a list of dictionaries with 'page' and 'content'.
        """
        pages_data = {}
        
        # Extract text items and group them by page
        for item in elements:
            # Unstructured elements store page_number in metadata
            page_no = item.metadata.page_number if item.metadata and item.metadata.page_number else 1
            
            if page_no not in pages_data:
                pages_data[page_no] = []
            
            if hasattr(item, "text") and item.text:
                pages_data[page_no].append(str(item.text))
        
        # Format into a structured list of sections
        structured_data = []
        for page_no, texts in pages_data.items():
            structured_data.append({
                "page": page_no,
                "content": "\n".join(texts)
            })
            
        return structured_data