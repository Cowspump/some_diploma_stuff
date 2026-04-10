from __future__ import annotations

import logging
import os
import re
import sys
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.argos_translate import translate as argos_translate
from api.gpt_client import client as openai_client

logger = logging.getLogger(__name__)


_RE_REPLACEMENT = re.compile(r"\ufffd")


def _looks_bad_translation(text: str) -> bool:
    """
    Very small heuristics to catch obvious garbage output.
    We only need to prevent cases like 'кракозябры' / replacement chars.
    """
    s = (text or "").strip()
    if not s:
        return True
    if _RE_REPLACEMENT.search(s):
        return True
    # Too many non-printable characters is suspicious
    non_printable = sum(1 for ch in s if ord(ch) < 9 or (13 < ord(ch) < 32))
    if non_printable > 0:
        return True
    return False


def _llm_translate(text: str, *, from_lang: str, to_lang: str) -> Optional[str]:
    try:
        from_lang = (from_lang or "").strip().lower() or "ru"
        to_lang = (to_lang or "").strip().lower() or "en"
        if from_lang == to_lang:
            return text

        lang_names = {"ru": "Russian", "en": "English", "zh": "Chinese"}
        from_name = lang_names.get(from_lang, from_lang)
        to_name = lang_names.get(to_lang, to_lang)

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator. "
                        "Preserve meaning, formatting (including newlines), and punctuation. "
                        "Return ONLY the translation, no quotes, no explanations."
                    ),
                },
                {"role": "user", "content": f"Translate this text from {from_name} to {to_name}:\n\n{text}"},
            ],
            max_tokens=1200,
            temperature=0.2,
        )
        out = (response.choices[0].message.content or "").strip()
        return out or None
    except Exception as e:
        logger.warning("LLM translation failed %s->%s: %s", from_lang, to_lang, e, exc_info=True)
        return None


def translate_hybrid(
    text: str,
    *,
    from_lang: str,
    to_lang: str,
    auto_install_models: bool = False,
) -> Optional[str]:
    """
    Hybrid translator: Argos first, fallback to LLM on failure or obvious garbage.
    """
    out = argos_translate(text, from_lang=from_lang, to_lang=to_lang, auto_install=auto_install_models)
    if out is None or _looks_bad_translation(out):
        llm_out = _llm_translate(text, from_lang=from_lang, to_lang=to_lang)
        return llm_out if llm_out is not None else out
    return out

