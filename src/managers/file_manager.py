"""
File Type Manager for Document Processing Pipeline

This module provides the central orchestration layer for document extraction operations
across multiple file formats. It implements a registry pattern for automatic extractor
discovery, handles dynamic loading of extractors based on dependencies, and provides
a unified interface for batch document processing.

Key Features:
    - Automatic extractor registration with graceful dependency handling
    - Type-safe file processing with comprehensive error handling
    - Extensible architecture for adding new document formats
    - Performance monitoring and detailed logging

Classes:
    FileTypeManager: Main orchestrator for document extraction operations
"""

import logging
from pathlib import Path
from typing import Union, Optional, Dict, Type

from src.extractors.base_extractor import BaseExtractor


class FileTypeManager:
    """
    Orchestrates data extraction from various document types.

    This class manages a collection of specialized extractors, each handling a specific
    file format. It provides automatic registration of available extractors at initialization,
    easy extension through custom extractor registration, and a unified interface for
    document processing.

    Attributes:
        logger (logging.Logger): Class-specific logger for operation tracking
        _extractors (Dict[str, Type[BaseExtractor]]): Registry mapping file extensions
            to their corresponding extractor classes
    """

    def __init__(self):
        """Initialize the manager with an empty extractor registry and register available extractors."""
        self.logger = logging.getLogger(self.__class__.__name__)

        # Maps file extensions to their corresponding extractor class
        self._extractors: Dict[str, Type[BaseExtractor]] = {}

        # Register all available extractors during initialization
        self._register_available_extractors()

    def _register_available_extractors(self):
        """
        Register all available extractors in the system.

        This method attempts to import each known extractor type and registers
        it if the required dependencies are available. The registration process
        is fault-tolerant - if an extractor's dependencies are missing, it logs
        a debug message and continues with other extractors.

        The method handles the following extractor types:
        - PDF (.pdf): Requires PyMuPDF (fitz) library
        - DOCX (.docx): Requires python-docx library
        - CSV (.csv): Uses standard library csv module
        - XLSX (.xlsx, .xlsm): Requires openpyxl and xlrd libraries
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
        Register a custom extractor for a specific file extension.

        This method allows for runtime registration of custom extractors, enabling
        the system to be extended without modifying core code. The extractor must
        implement the BaseExtractor interface to ensure compatibility.

        Args:
            extension (str): File extension to register, including the leading dot
                (e.g., '.pdf', '.txt', '.json'). Case-insensitive.
            extractor_class (Type[BaseExtractor]): Class that implements the
                BaseExtractor interface. Must be a subclass of BaseExtractor.

        Raises:
            ValueError: If the provided class doesn't inherit from BaseExtractor.
                This ensures type safety and interface compliance.
            TypeError: If extension is not a string or extractor_class is not a class.

        """
        if not issubclass(extractor_class, BaseExtractor):
            raise ValueError(f"{extractor_class.__name__} must inherit from BaseExtractor")

        extension = extension.lower()
        self._extractors[extension] = extractor_class
        self.logger.info(f"📝 Registered {extractor_class.__name__} for {extension}")

    def _create_extractor(self, file_path: Path) -> Optional[BaseExtractor]:
        """
        Create and return the appropriate extractor instance for a given file.

        This method serves as a factory function that determines the correct
        extractor based on the file's extension and instantiates it. The method
        handles instantiation errors gracefully and returns None if the extractor
        cannot be created.

        Args:
            file_path (Path): Path object representing the file to be processed.
                The file's extension is used for extractor selection.

        Returns:
            Optional[BaseExtractor]: An instantiated extractor object if the file
                type is supported and instantiation succeeds, None otherwise.

        Raises:
            No exceptions are raised. All instantiation errors are caught,
            logged, and result in a None return value.
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
        Process a document file through the complete extraction workflow.

        This is the main entry point for document processing. It handles the entire
        workflow from file validation through content extraction to result persistence.
        The method is designed to be robust and provide clear feedback about the
        processing status.

        Args:
            input_path (Union[str, Path]): Path to the input document file.
                Can be a string or Path object. Must point to an existing file.
            output_dir (Union[str, Path]): Directory where extraction results
                will be saved. Will be created if it doesn't exist.

        Returns:
            bool: True if the file was successfully processed and results saved,
                False if any step in the workflow failed.

        Raises:
            No exceptions are raised. All errors are caught, logged appropriately,
            and result in a False return value.

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
        Retrieve a list of all currently supported file extensions.

        This method provides visibility into the capabilities of the current
        manager instance. The returned list reflects the actual registered
        extractors and their supported file types.

        Returns:
            List[str]: List of file extensions (including leading dots) that
                can be processed by registered extractors. Extensions are in
                lowercase for consistency.
        """
        return list(self._extractors.keys())

    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """
        Check whether a specific file can be processed by available extractors.

        This method provides a quick way to validate file compatibility before
        attempting processing. It's particularly useful for filtering file lists
        and providing user feedback about supported formats.

        Args:
            file_path (Union[str, Path]): Path to the file to check.
                Can be a string or Path object. Only the extension is examined.

        Returns:
            bool: True if the file's extension is supported by a registered
                extractor, False otherwise.
        """
        extension = Path(file_path).suffix.lower()
        return extension in self._extractors

