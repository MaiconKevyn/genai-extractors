import sys
import logging
from pathlib import Path

project_root = Path.cwd()

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from config.settings import INPUT_DIR, OUTPUT_DIR, EXTRACTOR_CONFIG
from src.managers.file_manager import FileTypeManager
from src.extractors.pdf_extractor import PDFTextExtractor
from src.extractors.docx_extractor import DocxExtractor




AVAILABLE_EXTRACTORS = {
    '.pdf': PDFTextExtractor,
    '.docx': DocxExtractor,
    #'.xlsx': XLSXExtractor
}

manager = FileTypeManager()

logging.info(f"Registrando extratores suportados pela configuração: {EXTRACTOR_CONFIG.supported_extensions}")

for extension in EXTRACTOR_CONFIG.supported_extensions:
    extractor_class = AVAILABLE_EXTRACTORS.get(extension)
    if extractor_class:
        manager.register_extractor(extension, extractor_class)
    else:
        logging.warning(f"A extensão '{extension}' é suportada na configuração, mas não há uma classe de extrator mapeada para ela em AVAILABLE_EXTRACTORS.")
logging.info("="*50 + "\n")


logging.info(f"Iniciando processamento de arquivos do diretório: {INPUT_DIR}")
if not any(INPUT_DIR.iterdir()):
    logging.warning(f"O diretório de entrada '{INPUT_DIR}' está vazio.")
else:
    for file_path in sorted(INPUT_DIR.iterdir()):
        if file_path.is_file():
            logging.info(f"--- Processando: {file_path.name} ---")

            # O manager usa os caminhos importados
            success = manager.process_file(file_path, OUTPUT_DIR)

            if success:
                print(f"✅ Sucesso ao processar {file_path.name}")
            else:
                print(f"❌ Falha ou arquivo pulado: {file_path.name}")
            print("-" * 30 + "\n")

logging.info(f"Processamento concluído. Verifique os resultados em: {OUTPUT_DIR}")
