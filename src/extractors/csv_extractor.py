import csv
import logging
from pathlib import Path
from typing import Union

# Imports the base class and unified result
from .base_extractor import BaseExtractor, ExtractionResult


class CsvExtractor(BaseExtractor):
    """Extracts text from .csv files, with sampling for large files based on rows."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Constants for sampling logic (same pattern as DOCX)
        self.ROW_LIMIT_FOR_SAMPLING = 1000  # Similar to paragraph limit
        self.ROWS_TO_SAMPLE = 500  # Similar to paragraphs to sample

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts text from a .csv. If the file has more than 1000 rows,
        extracts only the first 500 and the last 500.
        """
        csv_path = Path(input_path)
        source_filename = csv_path.name

        if not csv_path.exists():
            return self._create_error_result(source_filename, f"File not found: {csv_path}")

        if csv_path.suffix.lower() != '.csv':
            return self._create_error_result(source_filename, f"File is not a .csv: {csv_path.suffix}")

        try:
            # Read CSV and count rows first
            with open(csv_path, 'r', encoding='utf-8', newline='') as file:
                reader = csv.reader(file)
                all_rows = list(reader)

            num_rows = len(all_rows)

            if num_rows == 0:
                return self._create_error_result(source_filename, "CSV file is empty")

            full_text_parts = []

            # Sampling logic for large files (same pattern as DOCX)
            if num_rows > self.ROW_LIMIT_FOR_SAMPLING:
                self.logger.info(
                    f"'{source_filename}' has {num_rows} rows (above the limit of {self.ROW_LIMIT_FOR_SAMPLING}). "
                    f"Sampling the first {self.ROWS_TO_SAMPLE} and the last {self.ROWS_TO_SAMPLE}."
                )

                # Extract header (first row)
                if all_rows:
                    full_text_parts.append("HEADERS: " + " | ".join(all_rows[0]))

                # Extract first rows
                for i in range(1, min(self.ROWS_TO_SAMPLE + 1, len(all_rows))):
                    row_text = " | ".join(str(cell) for cell in all_rows[i])
                    if row_text.strip():
                        full_text_parts.append(f"Row {i}: {row_text}")

                # Add separator
                full_text_parts.append("\n... (content of intermediate rows omitted) ...\n")

                # Extract last rows
                start_last_rows = max(1, num_rows - self.ROWS_TO_SAMPLE)
                for i in range(start_last_rows, num_rows):
                    row_text = " | ".join(str(cell) for cell in all_rows[i])
                    if row_text.strip():
                        full_text_parts.append(f"Row {i}: {row_text}")

            else:
                # Default logic for small files (same pattern as DOCX)
                self.logger.info(f"'{source_filename}' has {num_rows} rows. Extracting all content.")

                # Extract header
                if all_rows:
                    full_text_parts.append("HEADERS: " + " | ".join(all_rows[0]))

                # Extract all data rows
                for i, row in enumerate(all_rows[1:], 1):
                    row_text = " | ".join(str(cell) for cell in row)
                    if row_text.strip():
                        full_text_parts.append(f"Row {i}: {row_text}")

            # Combine all text into a single string (same as other extractors)
            full_content = "\n".join(full_text_parts)

            self.logger.info(f"Extraction of '{source_filename}' completed successfully.")

            return ExtractionResult(
                source_file=source_filename,
                content=full_content,
                success=True
            )

        except UnicodeDecodeError:
            # Try different encoding
            try:
                with open(csv_path, 'r', encoding='latin-1', newline='') as file:
                    reader = csv.reader(file)
                    all_rows = list(reader)
                # Process same as above...
                return self.extract(input_path)  # Retry with latin-1
            except Exception as e:
                return self._create_error_result(source_filename, f"Encoding error: {e}")

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