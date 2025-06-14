from dataclasses import dataclass
from pathlib import Path
from typing import Union, Optional


@dataclass
class ExtractionResult:
    """
    Unified data structure for extraction results.
    Contains the full content of the file as a single string.
    """
    source_file: str
    content: Optional[str]
    success: bool
    error_message: Optional[str] = None


class BaseExtractor:
    """
    Base class for all file extractors.
    Defines the interface that all extractors must follow.
    """

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts the content of a file and returns an ExtractionResult object.
        This method must be implemented by each extractor.
        """
        raise NotImplementedError("Each extractor must implement the 'extract' method.")

    def save_as_json(self, result: ExtractionResult, output_path: Union[str, Path]) -> bool:
        """
        Saves the content of an ExtractionResult to a JSON file.
        """
        import json
        import logging

        logger = logging.getLogger(self.__class__.__name__)
        output_path = Path(output_path)

        if not result.success:
            logger.error(
                f"Cannot save a result with error for '{result.source_file}'. Reason: {result.error_message}")
            return False

        try:
            # Ensure the output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            data_to_save = {
                "source_file": result.source_file,
                "content": result.content
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            logger.info(f"Result from '{result.source_file}' saved at: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving JSON to '{output_path}': {e}")
            return False

    def extract_and_save(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """
        Runs the complete process: extracts the content and saves it as JSON.
        This method orchestrates the call to 'extract' and 'save_as_json'.
        """
        result = self.extract(input_path)
        return self.save_as_json(result, output_path)