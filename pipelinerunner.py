# pipelinerunner.py
"""
Pipeline runner simplificado usando Factory Pattern.
Remove hard-coding e torna o código mais limpo.
"""

import sys
import logging
from pathlib import Path

# Setup do projeto
project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from config.settings import INPUT_DIR, OUTPUT_DIR, EXTRACTOR_CONFIG
from src.managers.file_manager import FileTypeManager

# ✅ Criação simplificada - factory auto-descobre extractors
manager = FileTypeManager()

# ✅ Log das extensões suportadas automaticamente
supported_extensions = manager.factory.get_supported_extensions()
logging.info(f"Supported extensions: {supported_extensions}")

# ✅ Verifica compatibilidade com configuração atual
config_extensions = EXTRACTOR_CONFIG.supported_extensions
unsupported = [ext for ext in config_extensions if ext not in supported_extensions]

if unsupported:
    logging.warning(f"Config references unsupported extensions: {unsupported}")
    logging.info(f"Available extractors: {supported_extensions}")

logging.info("=" * 50 + "\n")

# ✅ Processamento de arquivos (lógica permanece igual)
logging.info(f"Iniciando processamento de arquivos do diretório: {INPUT_DIR}")

if not INPUT_DIR.exists() or not any(INPUT_DIR.iterdir()):
    logging.warning(f"O diretório de entrada '{INPUT_DIR}' está vazio ou não existe.")
else:
    for file_path in sorted(INPUT_DIR.iterdir()):
        if file_path.is_file():
            # ✅ Verifica se arquivo é suportado antes de processar
            if manager.factory.is_supported(file_path):
                logging.info(f"--- Processando: {file_path.name} ---")
                success = manager.process_file(file_path, OUTPUT_DIR)

                if success:
                    print(f"✅ Sucesso ao processar {file_path.name}")
                else:
                    print(f"❌ Falha ao processar: {file_path.name}")
            else:
                logging.info(f"🚫 Arquivo não suportado: {file_path.name} ({file_path.suffix})")

            print("-" * 30 + "\n")

logging.info(f"Processamento concluído. Verifique os resultados em: {OUTPUT_DIR}")

# ✅ Estatísticas finais
total_files = len([f for f in INPUT_DIR.glob('*') if f.is_file()])
supported_files = len([f for f in INPUT_DIR.glob('*') if f.is_file() and manager.factory.is_supported(f)])

logging.info(f"📊 Estatísticas:")
logging.info(f"   Total de arquivos: {total_files}")
logging.info(f"   Arquivos suportados: {supported_files}")
logging.info(f"   Taxa de suporte: {supported_files / max(total_files, 1):.1%}")