import re
import string
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class TextQualityAnalyzer:
    """
    Analisa a qualidade do texto extraído e determina se precisa de processamento adicional.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o analisador com configurações personalizáveis.

        Args:
            config: Dicionário com configurações (min_length, max_replacement_ratio, etc.)
        """
        self.config = config or self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Configurações padrão - podem vir do config/settings.py futuramente."""
        return {
            'min_text_length': 50,
            'max_replacement_chars': 5,
            'min_word_count': 10,
            'max_replacement_ratio': 0.01,
            'min_ascii_ratio': 0.8
        }

    def analyze_quality(self, text: str) -> Dict[str, Any]:
        """
        Analisa a qualidade do texto e retorna métricas detalhadas.

        Returns:
            Dict com: is_poor_quality, metrics, recommendations
        """
        if not text:
            return {
                'is_poor_quality': True,
                'reason': 'empty_text',
                'metrics': {},
                'recommendations': ['Check input file', 'Try OCR if scanned document']
            }

        metrics = self._calculate_metrics(text)
        is_poor, reason = self._evaluate_quality(metrics)
        recommendations = self._get_recommendations(reason, metrics)

        result = {
            'is_poor_quality': is_poor,
            'reason': reason,
            'metrics': metrics,
            'recommendations': recommendations
        }

        if is_poor:
            logger.warning(f"Poor text quality detected: {reason}. Metrics: {metrics}")

        else:
            logger.warning(f"Good text quality detected: {reason}. Metrics: {metrics}")

        return result

    def _calculate_metrics(self, text: str) -> Dict[str, Any]:
        """Calcula métricas detalhadas do texto."""
        total_chars = len(text)

        # Contadores básicos
        replacement_chars = text.count('\ufffd')
        words = re.findall(r"\w+", text)
        word_count = len(words)

        # Caracteres ASCII vs Unicode
        ascii_count = sum(1 for c in text if ord(c) < 128)
        ascii_ratio = ascii_count / total_chars if total_chars > 0 else 0

        # Densidade de pontuação
        punct_count = sum(1 for c in text if c in string.punctuation)
        punct_ratio = punct_count / total_chars if total_chars > 0 else 0

        return {
            'total_chars': total_chars,
            'word_count': word_count,
            'replacement_chars': replacement_chars,
            'replacement_ratio': replacement_chars / total_chars if total_chars > 0 else 0,
            'ascii_ratio': ascii_ratio,
            'punctuation_ratio': punct_ratio,
            'avg_word_length': sum(len(w) for w in words) / max(word_count, 1)
        }

    def _evaluate_quality(self, metrics: Dict[str, Any]) -> tuple:
        """Avalia se a qualidade é pobre e identifica a razão principal."""

        # Texto muito curto
        if metrics['total_chars'] < self.config['min_text_length']:
            return True, 'too_short'

        # Muitos caracteres de substituição
        if metrics['replacement_chars'] > self.config['max_replacement_chars']:
            return True, 'too_many_replacement_chars'

        # Proporção alta de caracteres de substituição
        if metrics['replacement_ratio'] > self.config['max_replacement_ratio']:
            return True, 'high_replacement_ratio'

        # Poucas palavras
        if metrics['word_count'] < self.config['min_word_count']:
            return True, 'insufficient_words'

        # Baixa proporção ASCII (possível problema de encoding)
        if metrics['ascii_ratio'] < self.config['min_ascii_ratio']:
            return True, 'low_ascii_ratio'

        return False, 'good_quality'

    def _get_recommendations(self, reason: str, metrics: Dict[str, Any]) -> list:
        """Retorna recomendações baseadas na razão da má qualidade."""

        recommendations_map = {
            'empty_text': ['Check if file is valid', 'Verify file format'],
            'too_short': ['Check if document has content', 'Consider OCR for scanned images'],
            'too_many_replacement_chars': ['Use OCR for better character recognition', 'Check encoding'],
            'high_replacement_ratio': ['Apply OCR preprocessing', 'Verify source document quality'],
            'insufficient_words': ['Review extraction method', 'Try alternative parsing'],
            'low_ascii_ratio': ['Check text encoding', 'Consider language-specific processing'],
            'good_quality': ['No action needed']
        }

        return recommendations_map.get(reason, ['Manual review recommended'])
