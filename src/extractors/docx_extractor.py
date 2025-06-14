import docx  # Imports the python-docx library
import logging
from pathlib import Path
from typing import Union

# Imports the base class and unified result
from .base_extractor import BaseExtractor, ExtractionResult


class DocxExtractor(BaseExtractor):
    """Extracts text from .docx, with sampling for large files based on paragraphs."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Constants for sampling logic
        self.PARAGRAPH_LIMIT_FOR_SAMPLING = 180
        self.PARAGRAPHS_TO_SAMPLE = 90

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts text from a .docx. If the document has more than 150 paragraphs,
        extracts only the first 30 and the last 30.
        """
        docx_path = Path(input_path)
        source_filename = docx_path.name

        if not docx_path.exists():
            return self._create_error_result(source_filename, f"File not found: {docx_path}")

        if docx_path.suffix.lower() != '.docx':
            return self._create_error_result(source_filename, f"File is not a .docx: {docx_path.suffix}")

        try:
            document = docx.Document(str(docx_path))
            paragraphs = document.paragraphs
            num_paragraphs = len(paragraphs)

            full_text_parts = []

            # Sampling logic for large documents
            if num_paragraphs > self.PARAGRAPH_LIMIT_FOR_SAMPLING:
                self.logger.info(
                    f"'{source_filename}' has {num_paragraphs} paragraphs (above the limit of {self.PARAGRAPH_LIMIT_FOR_SAMPLING}). "
                    f"Sampling the first {self.PARAGRAPHS_TO_SAMPLE} and the last {self.PARAGRAPHS_TO_SAMPLE}."
                )

                # Extracts the first paragraphs
                for i in range(self.PARAGRAPHS_TO_SAMPLE):
                    if paragraphs[i].text.strip():
                        full_text_parts.append(paragraphs[i].text)

                # Adds a separator
                full_text_parts.append("\n\n... (content of intermediate paragraphs omitted) ...\n\n")

                # Extracts the last paragraphs
                start_last_paragraphs = num_paragraphs - self.PARAGRAPHS_TO_SAMPLE
                for i in range(start_last_paragraphs, num_paragraphs):
                    if paragraphs[i].text.strip():
                        full_text_parts.append(paragraphs[i].text)

            # Default logic for small or medium documents
            else:
                self.logger.info(f"'{source_filename}' has {num_paragraphs} paragraphs. Extracting all content.")
                # Extracts text from all paragraphs
                for para in paragraphs:
                    if para.text.strip():
                        full_text_parts.append(para.text)

                # Extracts text from all tables
                if document.tables:
                    for table in document.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                if cell.text.strip():
                                    full_text_parts.append(cell.text)

            # Combines all text into a single string
            full_content = "\n\n".join(full_text_parts)

            self.logger.info(f"Extraction of '{source_filename}' completed successfully.")

            return ExtractionResult(
                source_file=source_filename,
                content=full_content,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, f"Error processing file: {e}")

    def _create_error_result(self, source_file: str, error_message: str) -> ExtractionResult:
        """Creates a standardized error result."""
        self.logger.error(f"Error in file '{source_file}': {error_message}")
        return ExtractionResult(
            source_file=source_file,
            content=None,
            success=False,
            error_message=error_message
        )
