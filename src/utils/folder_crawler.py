import json
from config.settings import RAW_DIR, EXTRACTED_DIR, get_config_path

def create_folders():
    """
    Cria estrutura de pastas para raw e extracted com base no JSON de configuração.

    Estrutura criada:
    - RAW_DIR/{domain}/{category}/
    - EXTRACTED_DIR/{domain}/{category}/
    """
    # Carrega configuração
    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Cria estrutura para cada domínio e categoria usando diretórios centralizados
    for domain, categories in config.items():
        for category in categories.keys():
            # Usa RAW_DIR e EXTRACTED_DIR do settings
            (RAW_DIR / domain / category).mkdir(parents=True, exist_ok=True)
            (EXTRACTED_DIR / domain / category).mkdir(parents=True, exist_ok=True)

    print(f"✅ Estrutura criada: {len(config)} domínios, "
          f"{sum(len(cats) for cats in config.values())} categorias")

if __name__ == "__main__":
    create_folders()