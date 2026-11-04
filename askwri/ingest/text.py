"""Text matching shared by parsing and the audit: compare passages to a PDF's text layer."""

import re
import unicodedata


def comparable(text: str) -> str:
    """Letters and digits only, case-folded, ligatures expanded: what matching compares."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    return "".join(char for char in folded if char.isalnum())


def words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", text).casefold())


def missing_words(text: str, page_text: str) -> list[str]:
    """Words of the text that are not on the page, allowing for two words glued together."""
    page = comparable(page_text)
    return [word for word in words(text) if not _on_page(word, page)]


def _on_page(word: str, page: str) -> bool:
    return word in page or any(word[:i] in page and word[i:] in page for i in range(1, len(word)))
