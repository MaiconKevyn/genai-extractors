# src/extractors/base_extractor.py
"""
BaseExtractor simplificado.
Remove injeção de dependências desnecessária, mantém funcionalidade essencial.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Optional
from abc import ABC, abstractmethod


@dataclass
class ExtractionResult:
    """
    Estrutura unificada para resultados de extração.
    Contém o conteúdo completo do arquivo como string.
    """
    source_file: str
    content: Optional[str]
    success: bool
    error_message: Optional[str] = None


class BaseExtractor(ABC):
    """
    Classe base simplificada para extractors.
    Remove complexidade desnecessária, mantém funcionalidade essencial.
    """

    def __init__(self):
        """Inicialização simples com apenas logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extrai o conteúdo de um arquivo e retorna um ExtractionResult.
        Deve ser implementado por cada extractor.

        Args:
            input_path: Caminho do arquivo a extrair

        Returns:
            ExtractionResult com conteúdo extraído ou erro
        """
        pass

    def save_as_json(self, result: ExtractionResult, output_path: Union[str, Path]) -> bool:
        """
        Salva o conteúdo de um ExtractionResult em arquivo JSON.

        Args:
            result: Resultado da extração
            output_path: Caminho do arquivo de saída

        Returns:
            True se salvo com sucesso, False caso contrário
        """
        output_path = Path(output_path)

        if not result.success:
            self.logger.error(
                f"Não é possível salvar resultado com erro para '{result.source_file}'. "
                f"Motivo: {result.error_message}"
            )
            return False

        try:
            # Garante que o diretório de saída existe
            output_path.parent.mkdir(parents=True, exist_ok=True)

            data_to_save = {
                "source_file": result.source_file,
                "content": result.content
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Resultado de '{result.source_file}' salvo em: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao salvar JSON em '{output_path}': {e}")
            return False

    def extract_and_save(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """
        Executa o processo completo: extrai conteúdo e salva como JSON.

        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída

        Returns:
            True se processo concluído com sucesso, False caso contrário
        """
        result = self.extract(input_path)
        return self.save_as_json(result, output_path)

    def _create_error_result(self, source_file: str, error_message: str) -> ExtractionResult:
        """
        Método auxiliar para criar resultados de erro padronizados.

        Args:
            source_file: Nome do arquivo fonte
            error_message: Mensagem de erro

        Returns:
            ExtractionResult com erro
        """
        self.logger.error(f"Erro no arquivo '{source_file}': {error_message}")
        return ExtractionResult(
            source_file=source_file,
            content=None,
            success=False,
            error_message=error_message
        )