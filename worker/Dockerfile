FROM python:3.11-slim

WORKDIR /app

ENV HF_HOME="/app/.cache/huggingface"

COPY pyproject.toml .
COPY uv.lock .

RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --no-cache --no-install-package opencv-python

ENV PATH="/app/.venv/bin:$PATH"

RUN python -c "\
from docling.document_converter import DocumentConverter, PdfFormatOption; \
from docling.datamodel.pipeline_options import PdfPipelineOptions; \
from docling.datamodel.base_models import InputFormat; \
pipeline_options = PdfPipelineOptions(); \
pipeline_options.do_ocr = True; \
pipeline_options.generate_picture_images = True; \
pipeline_options.do_picture_description = True; \
DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)})"

COPY app/ .

CMD ["python", "processor.py"]