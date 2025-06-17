"""
PDF Document Text Extraction Module

This module provides specialized text extraction capabilities for PDF documents
using PyMuPDF (fitz) library. It implements sampling strategies for
large documents to balance performance with content coverage, making it suitable
for production environments with diverse document sizes.

Classes:
    PDFTextExtractor: Specialized extractor for PDF documents with intelligent sampling
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Union

from .base_extractor import BaseExtractor, ExtractionResult


class PDFTextExtractor(BaseExtractor):
    """
    Text extractor for PDF documents with intelligent processing strategies.

    This class specializes in extracting text content from PDF documents using the
    PyMuPDF library.The extractor implements a sampling strategy for large documents to
    maintain reasonable processing times while preserving representative content.

    Attributes:
        PAGE_LIMIT_FOR_SAMPLING (int): Threshold above which sampling is triggered.
            Documents with more pages will use sampling strategy.
        PAGES_TO_SAMPLE (int): Number of pages to extract from beginning and end
            when sampling is active.

    """

    def __init__(self):
        super().__init__()

        # Sampling settings for large files
        self.PAGE_LIMIT_FOR_SAMPLING = 10
        self.PAGES_TO_SAMPLE = 5

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extract text content from a PDF document with intelligent processing strategy.

        This method orchestrates the complete PDF text extraction workflow, including
        file validation, format verification, and content extraction. It automatically
        selects between full extraction and sampling based on document size.

        Args:
            input_path (Union[str, Path]): Path to the PDF file to process.
                Accepts both string paths and Path objects for flexibility.
                Must point to an existing, readable PDF file.

        Returns:
            ExtractionResult: Comprehensive result object containing:
                - source_file: Original filename for tracking
                - content: Extracted text content (None if failed)
                - success: Boolean extraction status
                - error_message: Detailed error info if extraction failed

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
        Core text extraction logic with intelligent sampling for large documents.

        This method implements the core extraction algorithm, automatically choosing
        between full extraction and sampling based on document size

        Sampling Strategy:
            - Documents ≤ 10 pages: Full extraction of all pages
            - Documents > 10 pages: Extract first 5 + last 5 pages
            - Content from middle pages is omitted with clear indicator
            - Empty pages are automatically filtered out

        Args:
            pdf_path (Path): Validated path to the PDF file
            source_filename (str): Original filename for logging purposes

        Returns:
            str: Extracted text content with proper page separation.
                Pages are joined with double newlines for readability.

        Raises:
            fitz.FileDataError: If PDF format is invalid or corrupted
            fitz.PasswordError: If PDF requires password authentication
            MemoryError: If document is too large for available memory
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