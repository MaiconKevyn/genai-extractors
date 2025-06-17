"""
Base Extractor Module for Document Processing Pipeline

This module provides the foundational abstract class and data structures for implementing
document extractors in the document processing pipeline. It establishes a consistent
interface and standardized result format across all extractor implementations.

Classes:
    ExtractionResult: Data structure for standardized extraction results
    BaseExtractor: Abstract base class for all document extractors
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Optional
from abc import ABC, abstractmethod


@dataclass
class ExtractionResult:
    """
    This dataclass provides a unified structure for communicating extraction
    outcomes across the entire pipeline, ensuring consistency and enabling
    robust error handling and result processing.


    Attributes:
        source_file (str): Original filename of the processed document
        content (Optional[str]): Extracted text content, None if extraction failed
        success (bool): Indicates whether extraction completed successfully
        error_message (Optional[str]): Detailed error description if success=False
        metadata (Dict[str, Any]): Additional extraction metadata (pages, size, etc.)

    """
    source_file: str
    content: Optional[str]
    success: bool
    error_message: Optional[str] = None

    def __post_init__(self):
        """Basic data validation"""
        if self.success and not self.content:
            self.success = False
            self.error_message = "Empty content despite success status"


class BaseExtractor(ABC):
    """
    Abstract base class for all document extractors in the pipeline.

    This class establishes the contract that all extractors must follow,
    providing essential shared functionality for logging, file validation,
    result persistence, and error handling. All concrete extractors should
    inherit from this class.

    Abstract Methods:
        extract: Must be implemented by all concrete extractors
    """

    def __init__(self):
        """Simple initialization with logger only"""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts content from a file.

        Args:
            input_path (Union[str, Path]): Path to the document file

        Returns:
            ExtractionResult: Standardized result containing extracted content
            or error information
        """

    def save_as_json(self, result: ExtractionResult, output_path: Union[str, Path]) -> bool:
        """
        Persist extraction result to a JSON file with standardized format.

        Saves the extraction result in a consistent JSON structure that can be
        easily processed by downstream analytics and monitoring systems. The
        output includes both content and metadata for comprehensive tracking.

        Args:
            result (ExtractionResult): The extraction result to save
            output_path (Union[str, Path]): Target file path for JSON output

        Returns:
            bool: True if file was saved successfully, False otherwise
        """
        output_path = Path(output_path)

        if not result.success:
            self.logger.error(
                f"Cannot save result with error for '{result.source_file}'. "
                f"Reason: {result.error_message}"
            )
            return False

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Simple and clean JSON structure
            data_to_save = {
                "source_file": result.source_file,
                "content": result.content,
                "extraction_info": {
                    "success": result.success,
                    "content_length": len(result.content) if result.content else 0
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Result saved: {output_path} ({len(result.content)} characters)")
            return True

        except Exception as e:
            self.logger.error(f"Error saving JSON to '{output_path}': {e}")
            return False

    def extract_and_save(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """
        Execute the complete extraction pipeline: extract content and save result.

        This is the main entry point for document processing, combining extraction
        and persistence in a single operation with comprehensive error handling
        and performance monitoring.

        Args:
            input_path (Union[str, Path]): Path to the input document
            output_path (Union[str, Path]): Path for the JSON output file

        Returns:
            bool: True if the entire pipeline completed successfully
        """
        self.logger.info(f"Starting extraction: {Path(input_path).name}")

        result = self.extract(input_path)

        if result.success:
            return self.save_as_json(result, output_path)
        else:
            self.logger.error(f"Extraction failed: {result.error_message}")
            return False

    def _create_error_result(self, source_file: str, error_message: str) -> ExtractionResult:
        """
        Helper method to create standardized error results.

        Args:
            source_file (str): Name of the source file that failed
            error_message (str): Detailed error description

        Returns:
            ExtractionResult: Standardized error result
        """
        self.logger.error(f"Error in file '{source_file}': {error_message}")
        return ExtractionResult(
            source_file=source_file,
            content=None,
            success=False,
            error_message=error_message
        )

    def _validate_file(self, file_path: Path, expected_extension: str) -> Optional[str]:
        """
        Perform standard file validation checks.

        Args:
            file_path (Path): Path to the file to validate
            expected_extension (str): Expected file extension (e.g., '.pdf')

        Returns:
            Optional[str]: None if valid, error message if invalid
        """
        if not file_path.exists():
            return f"File not found: {file_path}"

        if file_path.suffix.lower() != expected_extension.lower():
            return f"File is not {expected_extension}: {file_path.suffix}"

        if file_path.stat().st_size == 0:
            return f"File is empty: {file_path}"

        return None

