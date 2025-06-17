"""
Document Text Extraction Module

This module provides specialized text extraction capabilities for Microsoft Word
documents (.docx format) using the python-docx library.

Classes:
    DocxExtractor: Main class for DOCX text extraction with intelligent sampling
"""

import docx  # python-docx library
from pathlib import Path
from typing import Union

from .base_extractor import BaseExtractor, ExtractionResult


class DocxExtractor(BaseExtractor):
    """
    DOCX text extractor with intelligent sampling for large documents.

    This class specializes in extracting text content from Microsoft Word documents
    using the python-docx library. The extractor implements an intelligent sampling strategy for
    large documents to maintain reasonable processing times while preserving
    representative content from both text and tabular data.

    Attributes:
        PARAGRAPH_LIMIT_FOR_SAMPLING (int): Threshold above which sampling is triggered.
            Documents with more paragraphs will use sampling strategy.
        PARAGRAPHS_TO_SAMPLE (int): Number of paragraphs to extract from beginning
            and end when sampling is active.
    """

    def __init__(self):
        """Initialize the DOCX text extractor with optimized sampling configuration."""
        super().__init__()

        # Sampling settings for large files
        self.PARAGRAPH_LIMIT_FOR_SAMPLING = 180
        self.PARAGRAPHS_TO_SAMPLE = 90

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts text from DOCX using python-docx.

        This method orchestrates the complete DOCX text extraction workflow, including
        file validation, format verification, content extraction from both paragraphs
        and tables, and intelligent sampling for large documents.

        Args:
            input_path (Union[str, Path]): Path to the DOCX file to process.
                Accepts both string paths and Path objects for maximum flexibility.
                Must point to an existing, readable DOCX file.

        Returns:
            ExtractionResult: Comprehensive result object containing:
                - source_file: Original filename for tracking and logging
                - content: Extracted text content including tables (None if failed)
                - success: Boolean extraction status indicator
                - error_message: Detailed error information if extraction failed

        Raises:
            No exceptions are raised. All errors are caught and returned
            as failed ExtractionResult objects with descriptive error messages.
        """
        docx_path = Path(input_path)
        source_filename = docx_path.name

        # Basic validations
        if not docx_path.exists():
            return self._create_error_result(source_filename, f"File not found: {docx_path}")

        if docx_path.suffix.lower() != '.docx':
            return self._create_error_result(source_filename, f"File is not DOCX: {docx_path.suffix}")

        try:
            extracted_text = self._extract_text(docx_path, source_filename)

            return ExtractionResult(
                source_file=source_filename,
                content=extracted_text,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

    def _extract_text(self, docx_path: Path, source_filename: str) -> str:
        """
        Core text extraction logic with intelligent sampling for large documents.

        This method implements the comprehensive extraction algorithm that handles
        both paragraphs and tables while automatically choosing between full
        extraction and sampling based on document size. The algorithm is designed
        to maximize content fidelity while maintaining optimal performance.

        Args:
            docx_path (Path): Validated path to the DOCX file
            source_filename (str): Original filename for logging and error reporting

        Returns:
            str: Comprehensive extracted text content with proper formatting.
                Paragraphs and table content are separated with double newlines
                for optimal readability and structure preservation.

        Raises:
            docx.opc.exceptions.PackageNotFoundError: If DOCX format is invalid
            PermissionError: If file access is denied
            MemoryError: If document exceeds available memory capacity


        """
        document = docx.Document(str(docx_path))
        paragraphs = document.paragraphs
        num_paragraphs = len(paragraphs)

        full_text_parts = []

        # Sampling logic for large documents
        if num_paragraphs > self.PARAGRAPH_LIMIT_FOR_SAMPLING:
            self.logger.info(
                f"'{source_filename}' has {num_paragraphs} paragraphs. "
                f"Sampling the first {self.PARAGRAPHS_TO_SAMPLE} and last {self.PARAGRAPHS_TO_SAMPLE}."
            )

            # Extract first paragraphs
            for i in range(min(self.PARAGRAPHS_TO_SAMPLE, len(paragraphs))):
                if paragraphs[i].text.strip():
                    full_text_parts.append(paragraphs[i].text)

            # Add separator
            full_text_parts.append("\n\n... (intermediate paragraph content omitted) ...\n\n")

            # Extract last paragraphs
            start_last_paragraphs = max(0, num_paragraphs - self.PARAGRAPHS_TO_SAMPLE)
            for i in range(start_last_paragraphs, num_paragraphs):
                if paragraphs[i].text.strip():
                    full_text_parts.append(paragraphs[i].text)

        else:
            self.logger.info(f"'{source_filename}' has {num_paragraphs} paragraphs. Extracting all content.")

            # Extract text from all paragraphs
            for para in paragraphs:
                if para.text.strip():
                    full_text_parts.append(para.text)

            # Extract text from all tables
            if document.tables:
                for table in document.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                full_text_parts.append(cell.text)

        extracted_text = "\n\n".join(full_text_parts)
        self.logger.info(f"Extracted {len(extracted_text)} characters from '{source_filename}'")

        return extracted_text

