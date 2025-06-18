"""
CSV Data Extraction Module

This module provides text extraction for CSV (Comma-Separated Values) files
with character-based sampling for large datasets.

Classes:
    CSVTextExtractor: CSV text extractor with sampling
"""

import csv
from pathlib import Path
from typing import Union
from .base_extractor import BaseExtractor, ExtractionResult

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

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extract text from CSV file.

        Args:
            input_path: Path to CSV file

        Returns:
            ExtractionResult: Contains extracted text or error info
        """
        csv_path = Path(input_path)
        source_filename = csv_path.name

        if not csv_path.exists():
            return self._create_error_result(source_filename, f"File not found: {csv_path}")

        if csv_path.suffix.lower() != '.csv':
            return self._create_error_result(source_filename, f"File is not CSV: {csv_path.suffix}")

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                lines = [' '.join(row).strip() for row in reader if any(row)]

            full_text = "\n".join(lines)

            # Check if the total character count exceeds the limit
            if len(full_text) <= self.MAX_TOTAL_CHARACTERS:
                # No sampling needed, return full text
                sampled_text = full_text
            else:
                # Content is too large, sample the text
                sampled_text = self._sample_text(lines)

            return ExtractionResult(
                source_file=source_filename,
                content=sampled_text,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

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