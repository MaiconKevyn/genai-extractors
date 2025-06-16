import re
import string
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class TextQualityAnalyzer:
    """
    Analyzes the quality of extracted text and determines if additional processing is needed.
    Enhanced version with detailed scoring and settings from settings.py.
    """

    def __init__(self, config: Dict[str, Any] = None, debug_mode: bool = False):
        """
        Initializes the analyzer with customizable configurations.

        Args:
            config: Dictionary with configurations (min_length, max_replacement_ratio, etc.)
            debug_mode: If True, shows detailed scoring debug information
        """
        self.config = config or self._get_default_config()
        self.debug_mode = debug_mode

    def _get_default_config(self) -> Dict[str, Any]:
        """Default configurations - integrated with settings.py."""
        try:
            # Try to import configurations from settings.py
            from config.settings import get_quality_config
            return get_quality_config()
        except ImportError:
            # Fallback to hardcoded configurations
            return {
                'min_text_length': 50,
                'max_replacement_chars': 5,
                'min_word_count': 10,
                'max_replacement_ratio': 0.01,
                'min_ascii_ratio': 0.8,
                'ocr_threshold_score': 60.0,
                'severe_quality_threshold': 30.0
            }

    def analyze_quality(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text quality and returns detailed metrics.

        Returns:
            Dict with: is_poor_quality, needs_ocr, quality_score, metrics, recommendations
        """
        if not text:
            return {
                'is_poor_quality': True,
                'needs_ocr': True,
                'quality_score': 0,
                'quality_level': 'CRITICAL',
                'reason': 'empty_text',
                'metrics': {},
                'recommendations': ['Check input file', 'Try OCR if scanned document'],
                'scoring_breakdown': {'initial_score': 100, 'penalties': [], 'final_score': 0}
            }

        metrics = self._calculate_metrics(text)
        quality_score, scoring_breakdown = self._calculate_quality_score_with_debug(metrics)
        is_poor, reason = self._evaluate_quality(metrics, quality_score)
        needs_ocr = self._determine_ocr_need(quality_score, reason, metrics)
        quality_level = self._get_quality_level(quality_score)
        recommendations = self._get_recommendations(reason, metrics, needs_ocr)

        result = {
            'is_poor_quality': is_poor,
            'needs_ocr': needs_ocr,
            'quality_score': quality_score,
            'quality_level': quality_level,
            'reason': reason,
            'metrics': metrics,
            'recommendations': recommendations,
            'scoring_breakdown': scoring_breakdown
        }

        # Structured and clear logging
        self._log_quality_analysis(result)

        return result

    def _calculate_quality_score_with_debug(self, metrics: Dict[str, Any]) -> tuple:
        """
        Calculates score with detailed breakdown for debugging.

        Returns:
            tuple: (final_score, scoring_breakdown)
        """
        score = 100.0
        penalties = []

        if self.debug_mode:
            print(f"\nDEBUG SCORING:")
            print(f"   Starting score: {score}")
            print(f"   Metrics: {metrics}")

        # PENALTY 1: Text too short
        if metrics['total_chars'] < self.config['min_text_length']:
            penalty = 50
            score -= penalty
            penalties.append({
                'type': 'text_too_short',
                'penalty': penalty,
                'reason': f"Chars: {metrics['total_chars']} < {self.config['min_text_length']}",
                'remaining_score': score
            })
            if self.debug_mode:
                print(f"   -{penalty} points: Text too short ({metrics['total_chars']} chars)")

        # PENALTY 2: Replacement characters
        if metrics['replacement_ratio'] > 0:
            penalty = metrics['replacement_ratio'] * 5000
            score -= penalty
            penalties.append({
                'type': 'replacement_characters',
                'penalty': penalty,
                'reason': f"Replacement ratio: {metrics['replacement_ratio']:.3f}",
                'remaining_score': score
            })
            if self.debug_mode:
                print(f"   -{penalty:.1f} points: Replacement characters ({metrics['replacement_chars']} chars)")

        # PENALTY 3: Low ASCII ratio
        if metrics['ascii_ratio'] < self.config['min_ascii_ratio']:
            penalty = (self.config['min_ascii_ratio'] - metrics['ascii_ratio']) * 100
            score -= penalty
            penalties.append({
                'type': 'low_ascii_ratio',
                'penalty': penalty,
                'reason': f"ASCII ratio: {metrics['ascii_ratio']:.3f} < {self.config['min_ascii_ratio']}",
                'remaining_score': score
            })
            if self.debug_mode:
                print(f"   -{penalty:.1f} points: Low ASCII ratio ({metrics['ascii_ratio']:.3f})")

        # PENALTY 4: Few words
        if metrics['word_count'] < self.config['min_word_count']:
            penalty = 30
            score -= penalty
            penalties.append({
                'type': 'few_words',
                'penalty': penalty,
                'reason': f"Words: {metrics['word_count']} < {self.config['min_word_count']}",
                'remaining_score': score
            })
            if self.debug_mode:
                print(f"   -{penalty} points: Few words ({metrics['word_count']})")

        # PENALTY 5: Words too short
        if metrics['avg_word_length'] < 3:
            penalty = 20
            score -= penalty
            penalties.append({
                'type': 'short_words',
                'penalty': penalty,
                'reason': f"Avg word length: {metrics['avg_word_length']:.2f} < 3.0",
                'remaining_score': score
            })
            if self.debug_mode:
                print(f"   -{penalty} points: Short words ({metrics['avg_word_length']:.2f})")

        # PENALTY 6: Too much punctuation
        if metrics['punctuation_ratio'] > 0.3:
            penalty = 15
            score -= penalty
            penalties.append({
                'type': 'excessive_punctuation',
                'penalty': penalty,
                'reason': f"Punct ratio: {metrics['punctuation_ratio']:.3f} > 0.3",
                'remaining_score': score
            })
            if self.debug_mode:
                print(f"   -{penalty} points: Excessive punctuation ({metrics['punctuation_ratio']:.3f})")

        final_score = max(0.0, min(100.0, score))

        if self.debug_mode:
            print(f"   Final score: {final_score:.1f}/100")
            print(f"   Total penalties: {len(penalties)}")

        scoring_breakdown = {
            'initial_score': 100.0,
            'penalties': penalties,
            'raw_final_score': score,
            'final_score': final_score,
            'total_penalty': 100.0 - final_score
        }

        return final_score, scoring_breakdown

    def _calculate_metrics(self, text: str) -> Dict[str, Any]:
        """Calculates detailed text metrics."""
        total_chars = len(text)

        # Basic counters
        replacement_chars = text.count('\ufffd')
        words = re.findall(r"\w+", text)
        word_count = len(words)

        # ASCII vs Unicode characters
        ascii_count = sum(1 for c in text if ord(c) < 128)
        ascii_ratio = ascii_count / total_chars if total_chars > 0 else 0

        # Punctuation density
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

    def _evaluate_quality(self, metrics: Dict[str, Any], quality_score: float) -> tuple:
        """
        Evaluates if quality is poor and identifies the main reason.
        Now uses both metrics and calculated score.
        """
        # If the score is already very low, consider it poor
        if quality_score < self.config['ocr_threshold_score']:
            # Identifies the specific reason based on metrics
            if metrics['total_chars'] < self.config['min_text_length']:
                return True, 'too_short'
            elif metrics['replacement_chars'] > self.config['max_replacement_chars']:
                return True, 'too_many_replacement_chars'
            elif metrics['replacement_ratio'] > self.config['max_replacement_ratio']:
                return True, 'high_replacement_ratio'
            elif metrics['word_count'] < self.config['min_word_count']:
                return True, 'insufficient_words'
            elif metrics['ascii_ratio'] < self.config['min_ascii_ratio']:
                return True, 'low_ascii_ratio'
            else:
                return True, 'low_overall_quality'

        return False, 'good_quality'

    def _determine_ocr_need(self, quality_score: float, reason: str, metrics: Dict[str, Any]) -> bool:
        """
        Determines if the document needs OCR based on multiple factors.
        """
        # Very low score always indicates need for OCR
        if quality_score < self.config['ocr_threshold_score']:
            return True

        # Specific problems that indicate a scanned document
        ocr_indicators = [
            'too_many_replacement_chars',
            'high_replacement_ratio',
            'insufficient_words',
            'low_ascii_ratio'
        ]

        if reason in ocr_indicators:
            return True

        # Additional heuristic: very little text may indicate extraction failure
        if metrics.get('word_count', 0) < 20 and metrics.get('total_chars', 0) > 100:
            return True

        return False

    def _get_quality_level(self, score: float) -> str:
        """Converts numeric score to qualitative level."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 60:
            return "ACCEPTABLE"
        elif score >= 30:
            return "POOR"
        else:
            return "CRITICAL"

    def _get_recommendations(self, reason: str, metrics: Dict[str, Any], needs_ocr: bool) -> list:
        """Returns recommendations based on the complete analysis."""

        base_recommendations = {
            'empty_text': ['Check if file is valid', 'Verify file format'],
            'too_short': ['Check if document has content', 'Consider OCR for scanned images'],
            'too_many_replacement_chars': ['Use OCR for better character recognition', 'Check encoding'],
            'high_replacement_ratio': ['Apply OCR preprocessing', 'Verify source document quality'],
            'insufficient_words': ['Review extraction method', 'Try alternative parsing'],
            'low_ascii_ratio': ['Check text encoding', 'Consider language-specific processing'],
            'low_overall_quality': ['Multiple quality issues detected', 'Consider manual review'],
            'good_quality': ['No action needed']
        }

        recommendations = base_recommendations.get(reason, ['Manual review recommended'])

        # Add specific OCR recommendation if needed
        if needs_ocr and 'OCR' not in str(recommendations):
            recommendations.insert(0, 'PRIORITY: Apply OCR processing')

        return recommendations

    def _log_quality_analysis(self, result: Dict[str, Any]) -> None:
        """
        Generates clear and informative logs about the quality analysis.
        """
        quality_score = result['quality_score']
        quality_level = result['quality_level']
        needs_ocr = result['needs_ocr']
        reason = result['reason']

        # Main log - always visible
        ocr_status = "OCR NEEDED" if needs_ocr else "OCR NOT NEEDED"

        logger.info(
            f"QUALITY ANALYSIS: {ocr_status} | "
            f"Score: {quality_score:.1f}/100 | "
            f"Level: {quality_level} | "
            f"Reason: {reason}"
        )

        # Log breakdown if debug is active
        if self.debug_mode and result.get('scoring_breakdown'):
            breakdown = result['scoring_breakdown']
            logger.info(
                f"SCORING BREAKDOWN: {len(breakdown['penalties'])} penalties, total: -{breakdown['total_penalty']:.1f}")
            for penalty in breakdown['penalties']:
                logger.info(f"   • {penalty['type']}: -{penalty['penalty']:.1f} ({penalty['reason']})")

        # Detailed log if quality is problematic
        if result['is_poor_quality']:
            metrics = result['metrics']
            logger.warning(
                f"QUALITY DETAILS: "
                f"Words: {metrics.get('word_count', 0)}, "
                f"Chars: {metrics.get('total_chars', 0)}, "
                f"Replacement chars: {metrics.get('replacement_chars', 0)}, "
                f"ASCII ratio: {metrics.get('ascii_ratio', 0):.2f}"
            )

            # Specific recommendations
            recommendations = result['recommendations']
            logger.warning(f"RECOMMENDATIONS: {' | '.join(recommendations)}")

