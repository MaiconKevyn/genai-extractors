"""
PDF Document Text Extraction Module

This module provides text extraction for PDF documents using PyMuPDF (fitz) library.


Classes:
    PDFTextExtractor: PDF text extractor with sampling for large documents
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Union

from .base_extractor import BaseExtractor, ExtractionResult


class PDFTextExtractor(BaseExtractor):
    """
   Text extractor for PDF documents.

    Extracts text from PDF files using PyMuPDF. For large documents (>10 pages),
    samples first and last pages to limit processing time.

    Attributes:
        PAGE_LIMIT_FOR_SAMPLING (int): Page threshold for sampling (10)
        PAGES_TO_SAMPLE (int): Pages to extract from start/end when sampling (5)
    """

    def __init__(self):
        super().__init__()
        # Sampling settings for large files
        self.PAGE_LIMIT_FOR_SAMPLING = 10
        self.PAGES_TO_SAMPLE = 5

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extract text from PDF file.

        Args:
            input_path: Path to PDF file

        Raises:
            No exceptions are raised. All errors are caught and returned
            as failed ExtractionResult objects with descriptive messages.


        """
        pdf_path = Path(input_path)
        source_filename = pdf_path.name

        # Basic validations
        if not pdf_path.exists():
            return self._create_error_result(source_filename, f"File not found: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            return self._create_error_result(source_filename, f"File is not PDF: {pdf_path.suffix}")

        try:
            extracted_text = self._extract_text(pdf_path, source_filename)

            return ExtractionResult(
                source_file=source_filename,
                content=extracted_text,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

    def _extract_text(self, pdf_path: Path, source_filename: str) -> str:
        """
        Extract text with sampling for large documents.

        Sampling Strategy:
            - Documents ≤ 10 pages: Full extraction of all pages
            - Documents > 10 pages: Extract first 5 + last 5 pages
            - Empty pages are automatically filtered out

        Args:
            pdf_path (Path): Validated path to the PDF file
            source_filename (str): Original filename for logging purposes

        Returns:
            str: Extracted text content with proper page separation.
        """
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        page_texts = []

        # Sampling logic for large files
        if total_pages > self.PAGE_LIMIT_FOR_SAMPLING:
            self.logger.info(
                f"'{source_filename}' has {total_pages} pages. "
                f"Extracting the first {self.PAGES_TO_SAMPLE} and last {self.PAGES_TO_SAMPLE}."
            )

            # Extract first pages
            for i in range(self.PAGES_TO_SAMPLE):
                page_text = doc[i].get_text("text").strip()
                if page_text:
                    page_texts.append(page_text)

            # Add separator
            page_texts.append("\n\n... (intermediate pages content omitted) ...\n\n")

            # Extract last pages
            start_last_pages = total_pages - self.PAGES_TO_SAMPLE
            for i in range(start_last_pages, total_pages):
                page_text = doc[i].get_text("text").strip()
                if page_text:
                    page_texts.append(page_text)

        else:
            # Extract all pages for small files
            self.logger.info(f"'{source_filename}' has {total_pages} pages. Extracting all content.")
            for page in doc:
                page_text = page.get_text("text").strip()
                if page_text:
                    page_texts.append(page_text)

        doc.close()

        extracted_text = "\n\n".join(page_texts)
        self.logger.info(f"Extracted {len(extracted_text)} characters from '{source_filename}'")

        return extracted_text