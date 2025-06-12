import fitz  # PyMuPDF
import json
import logging
from pathlib import Path
from typing import List, Dict, Union, Optional, Type
from dataclasses import dataclass

class BaseExtractor:
    def extract_and_save(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        raise NotImplementedError("Cada extrator deve implementar este método.")

# --- Seu extrator de PDF, herdando de BaseExtractor ---
@dataclass
class ExtractionResult:
    """Resultado da extração de texto do PDF"""
    file_path: str
    pages: List[Dict[str, Union[int, str]]]
    total_pages: int
    success: bool
    error_message: Optional[str] = None