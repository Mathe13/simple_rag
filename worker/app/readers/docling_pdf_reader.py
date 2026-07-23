import logging
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

class Reader:
    """
    Uses Docling to extract raw elements and structure from a PDF.
    Explicitly enforces RapidOCR and enables the Vision-Language Model (VLM) 
    to generate text descriptions for diagrams and images.
    """
    def __init__(self):
        self.logger = logging.getLogger("worker.ingest.reader")
        
        pipeline_options = PdfPipelineOptions()
        
        #Enforce OCR settings
        pipeline_options.do_ocr = True
        
        #Enable VLM for Picture Descriptions
        pipeline_options.generate_picture_images = True
        pipeline_options.do_picture_description = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def extract_elements(self, file_path: str):
        """
        Converts the PDF into a Docling document object containing all elements,
        including AI-generated text descriptions of images.
        """
        self.logger.info(f"Extracting elements from {file_path} (OCR + VLM enabled)...")
        result = self.converter.convert(file_path)
        

        return result.document