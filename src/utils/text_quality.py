import re
import string
import logging

logger = logging.getLogger(__name__)


def needs_ocr(text):
    """
    Determine if extracted text is insufficient or garbled and needs OCR.
    Checks for emptiness, minimal length, too many unicode/gibberish, low ASCII ratio, and repetitive content.

    Args:
        text: Text to analyze

    Returns:
        bool: True if OCR is needed, False otherwise
    """
    if not text or len(text.strip()) < 50:
        return True

    total = len(text)

    # replacement/unrecognized character threshold (>1%)
    repl = text.count('\ufffd')
    if repl / total > 0.01:
        return True

    # ASCII vs unicode ratio
    ascii_count = sum(1 for c in text if ord(c) < 128)
    if ascii_count / total < 0.8:
        return True

    # unicode noise ratio
    unicode_count = sum(1 for c in text if ord(c) > 127)
    if unicode_count / total > 0.1:
        return True

    # control character presence (excluding common whitespace)
    ctrl_count = sum(1 for c in text if ord(c) < 32 and c not in ('\n', '\r', '\t'))
    if ctrl_count > 0:
        return True

    # word count heuristic
    words = re.findall(r"\w+", text)
    word_count = len(words)
    if word_count < 5 or word_count / total < 0.1:
        return True

    # average word length check
    avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
    if avg_word_len < 3:
        return True

    # punctuation density
    punct_count = sum(1 for c in text if c in string.punctuation)
    if punct_count / total > 0.3:
        return True

    # newline density
    if text.count('\n') / total > 0.1:
        return True

    # repetitive content: low unique char ratio
    if len(set(text)) / total < 0.3:
        return True

    return False


class TextQualityAnalyzer:
    """
    Simplified text quality analyzer that maintains compatibility with existing code.
    Uses only the needs_ocr heuristic - no complex scoring or configurations.
    """

    def __init__(self, config=None, debug_mode=False):
        """
        Simplified initialization - config and debug_mode are ignored for compatibility.

        Args:
            config: Ignored (kept for backward compatibility)
            debug_mode: Ignored (kept for backward compatibility)
        """
        pass

    def analyze_quality(self, text: str) -> dict:
        """
        Analyzes text quality using the simple needs_ocr heuristic.

        Args:
            text: Text to analyze

        Returns:
            dict: Simple result with needs_ocr boolean and basic info
        """
        if not text:
            logger.info("QUALITY: Empty text - OCR NEEDED")
            return {
                'needs_ocr': True,
                'reason': 'empty_text'
            }

        ocr_needed = needs_ocr(text)

        # Simple logging
        status = "OCR NEEDED" if ocr_needed else "OCR NOT NEEDED"
        char_count = len(text)
        word_count = len(re.findall(r"\w+", text))

        logger.info(f"QUALITY: {status} | Chars: {char_count} | Words: {word_count}")

        return {
            'needs_ocr': ocr_needed,
            'reason': 'quality_check_failed' if ocr_needed else 'good_quality'
        }