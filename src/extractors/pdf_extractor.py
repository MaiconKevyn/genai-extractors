import fitz  # PyMuPDF
import json
import logging
from pathlib import Path
from typing import List, Dict, Union, Optional
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Resultado da extração de texto do PDF"""
    file_path: str
    pages: List[Dict[str, Union[int, str]]]
    total_pages: int
    success: bool
    error_message: Optional[str] = None


class PDFTextExtractor:
    """Extrator de texto de PDF focado em simplicidade"""

    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configura logging básico"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def extract_text(self, pdf_path: Union[str, Path]) -> ExtractionResult:
        """
        Extrai texto de um PDF

        Args:
            pdf_path: Caminho para o arquivo PDF

        Returns:
            ExtractionResult com o texto extraído
        """
        pdf_path = Path(pdf_path)

        # Validações básicas
        if not pdf_path.exists():
            return self._create_error_result(
                str(pdf_path),
                f"Arquivo não encontrado: {pdf_path}"
            )

        if pdf_path.suffix.lower() != '.pdf':
            return self._create_error_result(
                str(pdf_path),
                f"Arquivo deve ser PDF, recebido: {pdf_path.suffix}"
            )

        try:
            self.logger.info(f"Iniciando extração: {pdf_path.name}")

            # Abre o PDF
            doc = fitz.open(str(pdf_path))

            if len(doc) == 0:
                doc.close()
                return self._create_error_result(
                    str(pdf_path),
                    "PDF vazio ou corrompido"
                )

            # Extrai texto de cada página
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().strip()

                pages.append({
                    "page_number": page_num + 1,
                    "text": text
                })

            total_pages = len(doc)
            doc.close()

            self.logger.info(f"Extração concluída: {pdf_path.name} ({total_pages} páginas)")

            return ExtractionResult(
                file_path=str(pdf_path),
                pages=pages,
                total_pages=total_pages,
                success=True
            )

        except Exception as e:
            self.logger.error(f"Erro na extração de {pdf_path.name}: {str(e)}")
            return self._create_error_result(str(pdf_path), str(e))

    def save_as_json(self, result: ExtractionResult, output_path: Union[str, Path]) -> bool:
        """
        Salva o resultado da extração como JSON

        Args:
            result: Resultado da extração
            output_path: Caminho onde salvar o arquivo JSON

        Returns:
            True se salvou com sucesso, False caso contrário
        """
        if not result.success:
            self.logger.error("Não é possível salvar resultado com erro")
            return False

        output_path = Path(output_path)

        # Garante que o diretório existe
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Garante extensão .json
        if output_path.suffix.lower() != '.json':
            output_path = output_path.with_suffix('.json')

        try:
            # Prepara dados para salvamento
            data = {
                "source_file": Path(result.file_path).name,
                "total_pages": result.total_pages,
                "pages": result.pages
            }

            # Salva arquivo JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"JSON salvo em: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao salvar JSON: {str(e)}")
            return False

    def extract_and_save(self, pdf_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """
        Extrai texto e salva como JSON em uma única operação

        Args:
            pdf_path: Caminho para o PDF
            output_path: Caminho para salvar o JSON

        Returns:
            True se toda operação foi bem-sucedida
        """
        result = self.extract_text(pdf_path)

        if not result.success:
            self.logger.error(f"Falha na extração: {result.error_message}")
            return False

        return self.save_as_json(result, output_path)

    def _create_error_result(self, file_path: str, error_message: str) -> ExtractionResult:
        """Cria um resultado de erro padronizado"""
        return ExtractionResult(
            file_path=file_path,
            pages=[],
            total_pages=0,
            success=False,
            error_message=error_message
        )


# ========== FUNÇÕES UTILITÁRIAS ==========

def extract_pdf_to_json(pdf_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    Função simples para extrair PDF e salvar como JSON

    Args:
        pdf_path: Caminho para o PDF
        output_path: Caminho para o JSON de saída

    Returns:
        True se bem-sucedido
    """
    extractor = PDFTextExtractor()
    return extractor.extract_and_save(pdf_path, output_path)


def extract_pdf_pages(pdf_path: Union[str, Path]) -> List[Dict]:
    """
    Extrai páginas de um PDF e retorna como lista

    Args:
        pdf_path: Caminho para o PDF

    Returns:
        Lista de dicionários com texto por página
    """
    extractor = PDFTextExtractor()
    result = extractor.extract_text(pdf_path)

    return result.pages if result.success else []