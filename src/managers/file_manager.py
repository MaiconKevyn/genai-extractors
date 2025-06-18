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
        self._extractors: Dict[str, Type[BaseExtractor]] = {}
        self._register_extractors()

    def _register_extractors(self):
        """Register available extractors."""
        registered = []

        # Try to register each extractor
        EXTRACTORS = [
            ('.pdf', 'src.extractors.pdf_extractor', 'PDFTextExtractor'),
            ('.docx', 'src.extractors.docx_extractor', 'DocxExtractor'),
            ('.csv', 'src.extractors.csv_extractor', 'CSVTextExtractor'),
            ('.xlsx', 'src.extractors.xlsx_extractor', 'XLSXTextExtractor'),
            ('.xlsm', 'src.extractors.xlsx_extractor', 'XLSXTextExtractor'),
            ('.xls', 'src.extractors.xlsx_extractor', 'XLSXTextExtractor'),
        ]

        for extension, module_name, class_name in EXTRACTORS:
            try:
                module = __import__(module_name, fromlist=[class_name])
                extractor_class = getattr(module, class_name)
                self._extractors[extension] = extractor_class
                registered.append(extension)
            except ImportError:
                self.logger.debug(f"Extractor for {extension} not available")

        if registered:
            self.logger.info(f"Available: {', '.join(registered)}")
        else:
            self.logger.warning("No extractors available")

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
            self.logger.error(f"Error creating {extractor_class.__name__}: {e}")
            return None

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

