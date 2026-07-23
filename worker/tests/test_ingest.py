import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from parsers.cleaner_parser import CleanerParser
from parsers.layout_parser import LayoutParser
from readers.unstructured_pdf_reader import Reader
from splitters.recursive_splitter import RecursiveSplitter
from processor import run_ingestion_pipeline


class TestCleanerParser:
    def test_clean_normal_text(self):
        cleaner = CleanerParser()
        data = [
            {"page": 1, "content": "  Hello    world!  \n\n  This is a test.  "}
        ]
        cleaned = cleaner.clean(data)
        assert len(cleaned) == 1
        assert cleaned[0]["page"] == 1
        assert cleaned[0]["content"] == "Hello world! This is a test."

    def test_clean_removes_cjk_characters(self):
        cleaner = CleanerParser()
        data = [
            {"page": 1, "content": "English text こんにちは 世界 Chinese 中文 text"}
        ]
        cleaned = cleaner.clean(data)
        assert len(cleaned) == 1
        assert "こんにちは" not in cleaned[0]["content"]
        assert "中文" not in cleaned[0]["content"]
        assert "English text" in cleaned[0]["content"]

    def test_clean_filters_header_footer_page_numbers(self):
        cleaner = CleanerParser()
        data = [
            {"page": 1, "content": "123"},
            {"page": 2, "content": "Valid section content here."}
        ]
        cleaned = cleaner.clean(data)
        assert len(cleaned) == 1
        assert cleaned[0]["page"] == 2
        assert cleaned[0]["content"] == "Valid section content here."


class TestLayoutParser:
    def test_group_elements(self):
        parser = LayoutParser()

        item1 = MagicMock()
        item1.metadata.page_number = 1
        item1.text = "Page 1 Line 1"

        item2 = MagicMock()
        item2.metadata.page_number = 1
        item2.text = "Page 1 Line 2"

        item3 = MagicMock()
        item3.metadata.page_number = 2
        item3.text = "Page 2 Line 1"

        elements = [item1, item2, item3]

        grouped = parser.group_elements(elements)
        assert len(grouped) == 2
        assert grouped[0] == {"page": 1, "content": "Page 1 Line 1\nPage 1 Line 2"}
        assert grouped[1] == {"page": 2, "content": "Page 2 Line 1"}

    def test_group_elements_fallback_page(self):
        parser = LayoutParser()

        item1 = MagicMock()
        item1.metadata.page_number = None
        item1.text = "Fallback line"

        elements = [item1]

        grouped = parser.group_elements(elements)
        assert len(grouped) == 1
        assert grouped[0] == {"page": 1, "content": "Fallback line"}


class TestRecursiveSplitter:
    @patch("splitters.recursive_splitter.RecursiveCharacterTextSplitter")
    def test_split(self, mock_splitter_class):
        mock_splitter_inst = MagicMock()
        mock_splitter_class.return_value = mock_splitter_inst
        mock_splitter_inst.split_documents.return_value = ["chunk1", "chunk2"]

        splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)
        cleaned_data = [{"page": 1, "content": "Sample content for splitting."}]

        chunks = splitter.split(cleaned_data, source_file="manual.pdf")
        assert chunks == ["chunk1", "chunk2"]
        mock_splitter_inst.split_documents.assert_called_once()
        docs = mock_splitter_inst.split_documents.call_args[0][0]
        assert len(docs) == 1
        assert docs[0].page_content == "Sample content for splitting."
        assert docs[0].metadata == {"source": "manual.pdf", "page": 1}


class TestReader:
    @patch("readers.unstructured_pdf_reader.partition_pdf")
    def test_extract_elements(self, mock_partition_pdf):
        mock_partition_pdf.return_value = ["mock_unstructured_element"]

        reader = Reader()
        elements = reader.extract_elements("test.pdf")

        assert elements == ["mock_unstructured_element"]
        mock_partition_pdf.assert_called_once_with(filename="test.pdf")


class TestPipeline:
    @patch("processor.PGVector")
    @patch("processor.OpenAIEmbeddings")
    @patch("processor.RecursiveSplitter")
    @patch("processor.CleanerParser")
    @patch("processor.LayoutParser")
    @patch("processor.Reader")
    @patch("processor.Path")
    def test_run_ingestion_pipeline_success(
        self,
        mock_path_class,
        mock_reader_class,
        mock_layout_parser_class,
        mock_cleaner_class,
        mock_splitter_class,
        mock_embeddings_class,
        mock_pgvector_class,
    ):
        mock_pdf = MagicMock(spec=Path)
        mock_pdf.name = "test.pdf"
        mock_pdf.__str__.return_value = "/opt/data/test.pdf"

        mock_dir = MagicMock()
        mock_dir.glob.return_value = [mock_pdf]
        mock_path_class.return_value = mock_dir

        mock_reader = MagicMock()
        mock_reader_class.return_value = mock_reader
        mock_reader.extract_elements.return_value = "unstructured_elements"

        mock_layout = MagicMock()
        mock_layout_parser_class.return_value = mock_layout
        mock_layout.group_elements.return_value = [{"page": 1, "content": "raw"}]

        mock_cleaner = MagicMock()
        mock_cleaner_class.return_value = mock_cleaner
        mock_cleaner.clean.return_value = [{"page": 1, "content": "cleaned"}]

        mock_splitter = MagicMock()
        mock_splitter_class.return_value = mock_splitter
        mock_chunk = MagicMock()
        mock_splitter.split.return_value = [mock_chunk]

        mock_vector_store = MagicMock()
        mock_pgvector_class.return_value = mock_vector_store

        run_ingestion_pipeline()

        mock_reader.extract_elements.assert_called_once_with("/opt/data/test.pdf")
        mock_layout.group_elements.assert_called_once_with("unstructured_elements")
        mock_cleaner.clean.assert_called_once_with([{"page": 1, "content": "raw"}])
        mock_splitter.split.assert_called_once_with([{"page": 1, "content": "cleaned"}], source_file="test.pdf")
        mock_pgvector_class.assert_called_once()
        mock_vector_store.add_documents.assert_called_once_with([mock_chunk])

    @patch("processor.PGVector")
    @patch("processor.Reader")
    @patch("processor.Path")
    def test_run_ingestion_pipeline_no_pdfs(
        self,
        mock_path_class,
        mock_reader_class,
        mock_pgvector_class,
    ):
        mock_dir = MagicMock()
        mock_dir.glob.return_value = []
        mock_path_class.return_value = mock_dir

        run_ingestion_pipeline()

        mock_reader_class.assert_called_once()
        mock_pgvector_class.assert_not_called()
