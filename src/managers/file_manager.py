"""
File Type Manager for Document Processing Pipeline

This module manages document extraction across multiple file formats.
Automatically discovers and registers available extractors based on dependencies.

Classes:
    FileTypeManager: Manages extractors for different file types
"""

import logging
from pathlib import Path
from typing import Union, Optional, Dict, Type

from src.extractors.base_extractor import BaseExtractor


class FileTypeManager:
    """
    Manages extractors for different document types.

    Automatically registers available extractors at initialization and provides
    methods to process files using the appropriate extractor.

    Attributes:
        logger (logging.Logger): Logger for operation tracking
        _extractors (Dict[str, Type[BaseExtractor]]): Maps file extensions to extractor classes
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Maps file extensions to their corresponding extractor class
        self._extractors: Dict[str, Type[BaseExtractor]] = {}

        # Register all available extractors during initialization
        self._register_available_extractors()

    def _register_available_extractors(self):
        """
        Register all available extractors based on installed dependencies.

        Attempts to import each extractor type and registers it if dependencies
        are available. Continues silently if dependencies are missing.
        """
        registered = []

        # PDF extractor registration
        try:
            from src.extractors.pdf_extractor import PDFTextExtractor
            self._extractors['.pdf'] = PDFTextExtractor
            registered.append('.pdf')
        except ImportError:
            self.logger.debug("PDF extractor not available - required dependencies may be missing")

        # DOCX extractor registration
        try:
            from src.extractors.docx_extractor import DocxExtractor
            self._extractors['.docx'] = DocxExtractor
            registered.append('.docx')
        except ImportError:
            self.logger.debug("DOCX extractor not available - required dependencies may be missing")

        # CSV extractor registration
        try:
            from src.extractors.csv_extractor import CSVTextExtractor
            self._extractors['.csv'] = CSVTextExtractor
            registered.append('.csv')
        except ImportError:
            self.logger.debug("CSV extractor not available - required dependencies may be missing")

        # XLSX extractor registration
        try:
            from src.extractors.xlsx_extractor import XLSXTextExtractor
            self._extractors['.xlsx'] = XLSXTextExtractor
            self._extractors['.xlsm'] = XLSXTextExtractor
            self._extractors['.xls'] = XLSXTextExtractor   # Legacy Excel format

            registered.append('.xlsx/.xlsm/.xls')
        except ImportError:
            self.logger.debug("Excel extractor not available - required dependencies may be missing")

        if registered:
            self.logger.info(f"✅ Registered extractors: {', '.join(registered)}")
        else:
            self.logger.warning("⚠️  No extractors available - check dependencies installation")

    def register_extractor(self, extension: str, extractor_class: Type[BaseExtractor]):
        """
        Register custom extractor for a file extension.

        Args:
            extension: File extension (e.g., '.pdf', '.txt')
            extractor_class: Class that inherits from BaseExtractor

        Raises:
            ValueError: If extractor_class doesn't inherit from BaseExtractor
        """
        if not issubclass(extractor_class, BaseExtractor):
            raise ValueError(f"{extractor_class.__name__} must inherit from BaseExtractor")

        extension = extension.lower()
        self._extractors[extension] = extractor_class
        self.logger.info(f"📝 Registered {extractor_class.__name__} for {extension}")

    def _create_extractor(self, file_path: Path) -> Optional[BaseExtractor]:
        """
        Create extractor instance for a file based on its extension.

        Args:
            file_path: Path to file

        Returns:
            Extractor instance or None if not supported/failed to create
        """
        extension = file_path.suffix.lower()

        extractor_class = self._extractors.get(extension)
        if not extractor_class:
            return None

        try:
            return extractor_class()
        except Exception as e:
            self.logger.error(f"❌ Error creating {extractor_class.__name__}: {e}")
            return None

    def process_file(self, input_path: Union[str, Path], output_dir: Union[str, Path]) -> bool:
        """
        Process document file and save extraction result.

        Args:
            input_path: Path to input document
            output_dir: Directory for output JSON file

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        input_path = Path(input_path)

        # Validate file existence
        if not input_path.exists():
            self.logger.error(f"File not found: {input_path}")
            return False

        try:
            # Create appropriate extractor based on file extension
            extractor = self._create_extractor(input_path)

            if extractor is None:
                self.logger.warning(
                    f"Unsupported file type: '{input_path.suffix}'. "
                    f"File ignored: '{input_path.name}'"
                )
                return False

            self.logger.info(f"Processing '{input_path.name}' with '{extractor.__class__.__name__}'")

            # Extract content and save to output directory
            output_path = Path(output_dir) / (input_path.stem + '.json')
            return extractor.extract_and_save(input_path, output_path)

        except Exception as e:
            self.logger.error(f"Unexpected error processing '{input_path.name}': {e}")
            return False

    def get_supported_extensions(self) -> list:
        """
        Get list of supported file extensions.

        Returns:
            List of file extensions (e.g., ['.pdf', '.docx', '.csv'])
        """
        return list(self._extractors.keys())

    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """
        Check if file type is supported.

        Args:
            file_path: Path to file to check

        Returns:
            bool: True if file extension is supported
        """
        extension = Path(file_path).suffix.lower()
        return extension in self._extractors

