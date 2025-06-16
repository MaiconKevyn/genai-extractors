# src/managers/file_manager.py
"""
FileTypeManager refatorado para usar Factory Pattern.
Mantém mesma interface pública, mas usa factory internamente.
"""

import logging
from pathlib import Path
from typing import Union, Optional

from src.extractors.factory import ExtractorFactory


class FileTypeManager:
    """
    Orchestrates the extraction of data from different file types.
    Agora usa Factory Pattern para criar extractors.
    """

    def __init__(self, factory: Optional[ExtractorFactory] = None):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Usa factory injetado ou cria um padrão
        if factory is None:
            from src.extractors.factory import get_default_factory
            self.factory = get_default_factory()
        else:
            self.factory = factory

    def register_extractor(self, extension: str, extractor_class):
        """
        Registra extractor (mantém compatibilidade com código atual).
        Agora delega para o factory.
        """
        self.factory.register(extension, extractor_class)
        self.logger.info(f"Registering extractor '{extractor_class.__name__}' for extension '{extension.lower()}'")

    def process_file(self, input_path: Union[str, Path], output_dir: Union[str, Path]) -> bool:
        """
        Processa arquivo usando factory para criar extractor.
        Mantém mesma assinatura e comportamento.
        """
        input_path = Path(input_path)

        try:
            # Factory cria extractor automaticamente
            extractor = self.factory.create_extractor(input_path)

            if extractor is None:
                self.logger.warning(f"No extractor registered for '{input_path.suffix}'. Skipping '{input_path.name}'.")
                return False

            self.logger.info(f"Processing '{input_path.name}' with '{extractor.__class__.__name__}'")

            # O resto do processamento permanece igual
            output_path = Path(output_dir) / (input_path.stem + '.json')
            return extractor.extract_and_save(input_path, output_path)

        except Exception as e:
            self.logger.error(f"Unexpected error while processing '{input_path.name}': {e}")
            return False