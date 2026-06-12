"""Lightweight machine-translation helpers.

Translates dynamic, English-authored content (chat answers, disease
descriptions, follow-up questions, etc.) to French on demand, using a free
Google Translate-backed library. All functions are no-ops when ``lang`` is
not ``"fr"``, and fail safe (return the original text) if the translation
request errors out (e.g. no network access).
"""

from __future__ import annotations

import functools
import logging

logger = logging.getLogger(__name__)

try:
    from deep_translator import GoogleTranslator
except ImportError:  # pragma: no cover - optional dependency
    GoogleTranslator = None

# Joined with this delimiter so a list of strings can be translated in a
# single request while preserving item boundaries.
_LIST_DELIM = "\n@@@\n"


@functools.lru_cache(maxsize=4096)
def _translate_to_french(text: str) -> str:
    if GoogleTranslator is None:
        return text
    try:
        return GoogleTranslator(source="auto", target="fr").translate(text)
    except Exception:
        logger.warning("French translation failed; returning original text", exc_info=True)
        return text


def translate_text(text: str | None, lang: str | None) -> str | None:
    """Translate a single string to French when ``lang == 'fr'``."""
    if lang != "fr" or not text or not isinstance(text, str) or not text.strip():
        return text
    return _translate_to_french(text)


def translate_list(items: list[str] | None, lang: str | None) -> list[str] | None:
    """Translate a list of strings to French in one batched request."""
    if lang != "fr" or not items:
        return items

    translatable = [i for i in items if isinstance(i, str) and i.strip()]
    if not translatable:
        return items

    joined = _LIST_DELIM.join(translatable)
    translated = _translate_to_french(joined)
    parts = [p.strip() for p in translated.split(_LIST_DELIM.strip())]

    if len(parts) != len(translatable):
        # Delimiter didn't survive translation intact — fall back to
        # translating each item individually.
        parts = [_translate_to_french(item) for item in translatable]

    result = []
    it = iter(parts)
    for item in items:
        if isinstance(item, str) and item.strip():
            result.append(next(it))
        else:
            result.append(item)
    return result
