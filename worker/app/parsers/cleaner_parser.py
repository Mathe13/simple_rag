import re

class CleanerParser:
    """
    Cleans the parsed sections by removing unwanted characters, headers, and footers.
    """
    def __init__(self):
        # Regex to match CJK (Chinese, Japanese, Korean) characters
        self.cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+')

    def clean(self, structured_data):
        cleaned_data = []
        
        for section in structured_data:
            content = section["content"]
            
            # Remove non-normal characters (e.g., Chinese, Japanese)
            content = self.cjk_pattern.sub('', content)
            
            # Remove redundant whitespaces and newlines
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Basic heuristic to drop likely headers/footers (e.g., standalone page numbers)
            if len(content) < 5 and content.isdigit():
                continue
                
            if content:
                cleaned_data.append({
                    "page": section["page"],
                    "content": content
                })
                
        return cleaned_data