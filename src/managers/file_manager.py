import logging
from pathlib import Path
from typing import Union, Dict, Type, Optional, List
from extractors.base_extractor import BaseExtractor, ExtractionResult, FileType
from extractors.pdf_extractor import PDFTextExtractor
from utils.file_detection import FileDetector


class FileTypeManager:
    """Manager principal que coordena extração baseada no tipo de arquivo"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.file_detector = FileDetector()

        # Registry de extratores
        self._extractors: Dict[FileType, Type[BaseExtractor]] = {
            FileType.PDF: PDFTextExtractor,
            # FileType.CSV: CSVExtractor,      # Futuro
            # FileType.XLSX: XLSXExtractor,    # Futuro
            # FileType.JSON: JSONExtractor,    # Futuro
        }

        # Cache de instâncias
        self._extractor_instances: Dict[FileType, BaseExtractor] = {}

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def extract_file(self, file_path: Union[str, Path]) -> ExtractionResult:
        """
        Extrai conteúdo de qualquer arquivo suportado

        Args:
            file_path: Caminho para o arquivo

        Returns:
            ExtractionResult com o conteúdo extraído
        """
        file_path = Path(file_path)

        # Detecta tipo do arquivo
        file_type = self.file_detector.detect_file_type(file_path)

        if file_type == FileType.UNKNOWN:
            return ExtractionResult(
                file_path=str(file_path),
                file_type=file_type,
                content=None,
                metadata={},
                success=False,
                error_message=f"Tipo de arquivo não suportado: {file_path.suffix}"
            )

        # Obtém extrator apropriado
        extractor = self._get_extractor(file_type)

        if not extractor:
            return ExtractionResult(
                file_path=str(file_path),
                file_type=file_type,
                content=None,
                metadata={},
                success=False,
                error_message=f"Extrator não disponível para tipo: {file_type.value}"
            )

        # Executa extração
        self.logger.info(f"Usando {extractor.__class__.__name__} para {file_path.name}")
        return extractor.extract(file_path)

    def extract_and_save(self, file_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """
        Extrai arquivo e salva como JSON

        Args:
            file_path: Arquivo de entrada
            output_path: Caminho de saída

        Returns:
            True se bem-sucedido
        """
        result = self.extract_file(file_path)

        if not result.success:
            self.logger.error(f"Falha na extração: {result.error_message}")
            return False

        # Usa o extrator apropriado para salvar
        extractor = self._get_extractor(result.file_type)
        return extractor.save_as_json(result, output_path)

    def _get_extractor(self, file_type: FileType) -> Optional[BaseExtractor]:
        """Obtém instância do extrator para o tipo de arquivo"""
        if file_type not in self._extractors:
            return None

        # Usa cache de instâncias
        if file_type not in self._extractor_instances:
            extractor_class = self._extractors[file_type]
            self._extractor_instances[file_type] = extractor_class()

        return self._extractor_instances[file_type]

    def get_supported_types(self) -> List[FileType]:
        """Retorna tipos de arquivo suportados"""
        return list(self._extractors.keys())

    def register_extractor(self, file_type: FileType, extractor_class: Type[BaseExtractor]):
        """Registra novo extrator (para extensibilidade)"""
        self._extractors[file_type] = extractor_class
        # Remove do cache se existir
        if file_type in self._extractor_instances:
            del self._extractor_instances[file_type]

        self.logger.info(f"Extrator registrado: {file_type.value} -> {extractor_class.__name__}")