from extractors.pdf_extractor import PDFTextExtractor
from pathlib import Path
from typing import Union

class FileTypeManager:
    def __init__(self):
        self.extractors = {
            '.pdf': PDFTextExtractor,
            # '.csv': CSVExtractor,
            # '.xlsx': XLSXExtractor,
        }

    def process(self, input_file_path: str) -> bool:
        path = Path(input_file_path)
        ext = path.suffix.lower()

        extractor_class = self.extractors.get(ext)
        if extractor_class is None:
            print(f"Nenhum extrator disponível para arquivos com extensão '{ext}'.")
            return False

        try:
            extractor = extractor_class()

            # Define caminho de saída automático
            output_path = Path("data/output") / (path.stem + ".json")

            # Extrai e salva
            return extractor.extract_and_save(path, output_path)

        except Exception as e:
            print(f"Erro ao processar {path.name}: {e}")
            return False