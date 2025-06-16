# src/extractors/factory.py
"""
Factory Pattern simples para criação de extractors.
Substitui o hard-coding atual mantendo a mesma funcionalidade.
"""

import logging
from pathlib import Path
from typing import Dict, Type, Optional, Union

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """
    Factory simples para criar extractors baseado na extensão do arquivo.
    Centraliza a lógica de criação que estava espalhada.
    """

    def __init__(self):
        self._extractors: Dict[str, Type[BaseExtractor]] = {}
        self._auto_register_extractors()

    def _auto_register_extractors(self):
        """Auto-registra extractors disponíveis."""
        registered = []

        # Tenta registrar PDF extractor
        try:
            from .pdf_extractor import PDFTextExtractor
            self.register('.pdf', PDFTextExtractor)
            registered.append('.pdf')
        except ImportError:
            logger.debug("PDF extractor not available")

        # Tenta registrar DOCX extractor
        try:
            from .docx_extractor import DocxExtractor
            self.register('.docx', DocxExtractor)
            registered.append('.docx')
        except ImportError:
            logger.debug("DOCX extractor not available")

        # Tenta registrar CSV extractor
        try:
            from .csv_extractor import CsvExtractor
            self.register('.csv', CsvExtractor)
            registered.append('.csv')
        except ImportError:
            logger.debug("CSV extractor not available")

        # Tenta registrar XLSX extractor
        try:
            from .xlsx_extractor import XlsxExtractor
            self.register('.xlsx', XlsxExtractor)
            self.register('.xlsm', XlsxExtractor)  # Suporte a macros também
            registered.append('.xlsx')
        except ImportError:
            logger.debug("XLSX extractor not available")

        if registered:
            logger.info(f"✅ Auto-registered extractors: {', '.join(registered)}")
        else:
            logger.warning("⚠️  No extractors could be auto-registered")

    def register(self, extension: str, extractor_class: Type[BaseExtractor]):
        """
        Registra um extractor para uma extensão.

        Args:
            extension: Extensão (ex: '.pdf')
            extractor_class: Classe do extractor
        """
        if not issubclass(extractor_class, BaseExtractor):
            raise ValueError(f"{extractor_class.__name__} must inherit from BaseExtractor")

        normalized_ext = extension.lower()
        self._extractors[normalized_ext] = extractor_class
        logger.debug(f"📝 Registered {extractor_class.__name__} for {normalized_ext}")

    def create_extractor(self, file_path: Union[str, Path]) -> Optional[BaseExtractor]:
        """
        Cria extractor apropriado para um arquivo.

        Args:
            file_path: Caminho do arquivo

        Returns:
            Instância do extractor ou None se não suportado
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        extractor_class = self._extractors.get(extension)

        if not extractor_class:
            logger.debug(f"No extractor for {extension}")
            return None

        try:
            extractor = extractor_class()
            logger.debug(f"✅ Created {extractor_class.__name__} for {file_path.name}")
            return extractor

        except Exception as e:
            logger.error(f"❌ Failed to create {extractor_class.__name__}: {e}")
            return None

    def get_supported_extensions(self) -> list:
        """Retorna lista de extensões suportadas."""
        return list(self._extractors.keys())

    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """Verifica se um arquivo é suportado."""
        extension = Path(file_path).suffix.lower()
        return extension in self._extractors


# Instância global para facilitar uso
_default_factory = None


def get_default_factory() -> ExtractorFactory:
    """Retorna factory padrão (singleton)."""
    global _default_factory
    if _default_factory is None:
        _default_factory = ExtractorFactory()
    return _default_factory