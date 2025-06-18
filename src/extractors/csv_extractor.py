"""
CSV Data Extraction Module

This module provides text extraction for CSV (Comma-Separated Values) files
with character-based sampling for large datasets.

Classes:
    CSVTextExtractor: CSV text extractor with sampling
"""

import csv
from pathlib import Path
from typing import Union, Optional
from .base_extractor import BaseExtractor

class CSVTextExtractor(BaseExtractor):
    """
    Text extractor for CSV files.

    Extracts text from CSV files by joining row cells with spaces.
    For large files (>30,000 characters), samples first and last portions.

    Attributes:
        MAX_TOTAL_CHARACTERS (int): Character limit for extracted content (30,000)
    """

    MAX_TOTAL_CHARACTERS = 30000  # Approximate size limit (~10 pages)

    def __init__(self):
        super().__init__()

    def extract(self, input_path: Union[str, Path]) -> Optional[str]:
        """
        Extract text from CSV file.

        Args:
            input_path: Path to CSV file

        Returns:
            Optional[str]: Extracted text content if successful, None if extraction failed.
        """
        csv_path = Path(input_path)
        source_filename = csv_path.name

        # Validate file using inherited method
        validation_error = self._validate_file(csv_path, '.csv')
        if validation_error:
            self.logger.error(f"CSV validation failed for '{source_filename}': {validation_error}")
            return None

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                lines = [' '.join(row).strip() for row in reader if any(row)]

            full_text = "\n".join(lines)

            # Check if the total character count exceeds the limit
            if len(full_text) <= self.MAX_TOTAL_CHARACTERS:
                # No sampling needed, return full text
                sampled_text = full_text
                self.logger.info(f"'{source_filename}' extracted in full ({len(full_text)} characters)")

            else:
                # Content is too large, sample the text
                sampled_text = self._sample_text(lines)
                self.logger.info(f"'{source_filename}' sampled due to size ({len(sampled_text)} characters)")

            return sampled_text


        except Exception as e:
            self.logger.error(f"CSV extraction failed for '{source_filename}': {e}")
            return None

    def _sample_text(self, lines: list[str]) -> str:
        """
        Sample text from start and end when content exceeds limit.

        Args:
            lines: All text lines from CSV

        Returns:
            str: Sampled content with separator indicating omitted middle content
        """
        half_limit = self.MAX_TOTAL_CHARACTERS // 2
        start, end = [], []

        # Collect lines from the start until half limit is reached
        char_count = 0
        for line in lines:
            if char_count + len(line) > half_limit:
                break
            start.append(line)
            char_count += len(line)

        # Collect lines from the end until half limit is reached
        char_count = 0
        for line in reversed(lines):
            if char_count + len(line) > half_limit:
                break
            end.insert(0, line)
            char_count += len(line)

        # Combine start and end with ellipsis in the middle
        return "\n".join(start + ["..."] + end)