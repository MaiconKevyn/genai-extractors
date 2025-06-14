import logging
from pathlib import Path
from typing import Union, Dict, Type

from src.extractors.base_extractor import BaseExtractor


class FileTypeManager:
    """Orchestrates the extraction of data from different file types."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._extractors: Dict[str, Type[BaseExtractor]] = {}

    def register_extractor(self, extension: str, extractor_class: Type[BaseExtractor]):
        normalized_extension = extension.lower()
        self.logger.info(f"Registering extractor '{extractor_class.__name__}' for extension '{normalized_extension}'")
        self._extractors[normalized_extension] = extractor_class

    def process_file(self, input_path: Union[str, Path], output_dir: Union[str, Path]) -> bool:
        input_path = Path(input_path)
        extension = input_path.suffix.lower()
        extractor_class = self._extractors.get(extension)

        if not extractor_class:
            self.logger.warning(f"No extractor registered for '{extension}'. Skipping '{input_path.name}'.")
            return False

        try:
            self.logger.info(f"Processing '{input_path.name}' with '{extractor_class.__name__}'")
            extractor = extractor_class()

            # The output filename continues to be generated in the same way
            output_path = Path(output_dir) / (input_path.stem + '.json')

            # The call to the extractor remains the same
            return extractor.extract_and_save(input_path, output_path)
        except Exception as e:
            self.logger.error(f"Unexpected error while processing '{input_path.name}': {e}")
            return False
