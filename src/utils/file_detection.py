import mimetypes
from pathlib import Path
from typing import Union
from extractors.base_extractor import FileType


class FileDetector:
    """Utilitário para detectar tipo de arquivo"""

    def __init__(self):
        # Mapeamento de extensões para tipos
        self._extension_map = {
            '.pdf': FileType.PDF,
            '.csv': FileType.CSV,
            '.xlsx': FileType.XLSX,
            '.xls': FileType.XLSX,
            '.json': FileType.JSON,
        }

    def detect_file_type(self, file_path: Union[str, Path]) -> FileType:
        """
        Detecta tipo do arquivo baseado na extensão

        Args:
            file_path: Caminho do arquivo

        Returns:
            FileType identificado
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        return self._extension_map.get(extension, FileType.UNKNOWN)

    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """Verifica se o arquivo é suportado"""
        return self.detect_file_type(file_path) != FileType.UNKNOWN
