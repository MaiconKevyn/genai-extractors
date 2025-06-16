# src/managers/file_manager.py
"""
FileTypeManager simplificado - sem Factory Pattern.
Mantém a mesma funcionalidade com código mais direto e simples.
"""

import logging
from pathlib import Path
from typing import Union, Optional, Dict, Type

from src.extractors.base_extractor import BaseExtractor


class FileTypeManager:
    """
    Orquestra a extração de dados de diferentes tipos de arquivos.
    Versão simplificada que mapeia extensões diretamente para extractors.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Mapeamento direto: extensão -> classe do extractor
        self._extractors: Dict[str, Type[BaseExtractor]] = {}

        # Auto-registra extractors disponíveis na inicialização
        self._register_available_extractors()

    def _register_available_extractors(self):
        """
        Registra automaticamente extractors disponíveis.
        Centraliza imports e registros em um só lugar.
        """
        registered = []

        # Registra PDF extractor se disponível
        try:
            from src.extractors.pdf_extractor import PDFTextExtractor
            self._extractors['.pdf'] = PDFTextExtractor
            registered.append('.pdf')
        except ImportError:
            self.logger.debug("PDF extractor not available")

        # Registra DOCX extractor se disponível
        try:
            from src.extractors.docx_extractor import DocxExtractor
            self._extractors['.docx'] = DocxExtractor
            registered.append('.docx')
        except ImportError:
            self.logger.debug("DOCX extractor not available")

        # Registra CSV extractor se disponível
        try:
            from src.extractors.csv_extractor import CsvExtractor
            self._extractors['.csv'] = CsvExtractor
            registered.append('.csv')
        except ImportError:
            self.logger.debug("CSV extractor not available")

        # Registra XLSX extractor se disponível
        try:
            from src.extractors.xlsx_extractor import XlsxExtractor
            self._extractors['.xlsx'] = XlsxExtractor
            self._extractors['.xlsm'] = XlsxExtractor  # Suporte a macros
            registered.append('.xlsx/.xlsm')
        except ImportError:
            self.logger.debug("XLSX extractor not available")

        if registered:
            self.logger.info(f"✅ Registered extractors: {', '.join(registered)}")
        else:
            self.logger.warning("⚠️  No extractors available")

    def register_extractor(self, extension: str, extractor_class: Type[BaseExtractor]):
        """
        Registra um extractor customizado para uma extensão.
        Mantém compatibilidade com código existente.

        Args:
            extension: Extensão do arquivo (ex: '.pdf')
            extractor_class: Classe do extractor
        """
        if not issubclass(extractor_class, BaseExtractor):
            raise ValueError(f"{extractor_class.__name__} deve herdar de BaseExtractor")

        extension = extension.lower()
        self._extractors[extension] = extractor_class
        self.logger.info(f"📝 Registered {extractor_class.__name__} for {extension}")

    def _create_extractor(self, file_path: Path) -> Optional[BaseExtractor]:
        """
        Cria extractor apropriado para um arquivo.
        Lógica simples: pega a extensão e instancia a classe correspondente.

        Args:
            file_path: Caminho do arquivo

        Returns:
            Instância do extractor ou None se não suportado
        """
        extension = file_path.suffix.lower()

        extractor_class = self._extractors.get(extension)
        if not extractor_class:
            return None

        try:
            return extractor_class()
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar {extractor_class.__name__}: {e}")
            return None

    def process_file(self, input_path: Union[str, Path], output_dir: Union[str, Path]) -> bool:
        """
        Processa arquivo criando o extractor diretamente.
        Mantém mesma assinatura e comportamento da versão anterior.

        Args:
            input_path: Caminho do arquivo de entrada
            output_dir: Diretório de saída

        Returns:
            True se processado com sucesso, False caso contrário
        """
        input_path = Path(input_path)

        # Valida se arquivo existe
        if not input_path.exists():
            self.logger.error(f"Arquivo não encontrado: {input_path}")
            return False

        try:
            # Cria extractor baseado na extensão
            extractor = self._create_extractor(input_path)

            if extractor is None:
                self.logger.warning(
                    f"Tipo de arquivo não suportado: '{input_path.suffix}'. "
                    f"Arquivo ignorado: '{input_path.name}'"
                )
                return False

            self.logger.info(f"Processando '{input_path.name}' com '{extractor.__class__.__name__}'")

            # Processa arquivo
            output_path = Path(output_dir) / (input_path.stem + '.json')
            return extractor.extract_and_save(input_path, output_path)

        except Exception as e:
            self.logger.error(f"Erro inesperado ao processar '{input_path.name}': {e}")
            return False

    def get_supported_extensions(self) -> list:
        """Retorna lista de extensões suportadas."""
        return list(self._extractors.keys())

    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """Verifica se um arquivo é suportado."""
        extension = Path(file_path).suffix.lower()
        return extension in self._extractors