from __future__ import annotations

import re


_RE_HAN = re.compile(r"[\u4e00-\u9fff]")
_RE_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
_RE_LATIN = re.compile(r"[A-Za-z]")


def detect_ru_en_zh(text: str) -> str:
    """
    Best-effort detector for RU/EN/ZH for short UI content.
    Returns: 'ru' | 'en' | 'zh'
    """
    s = (text or "").strip()
    if not s:
        return "ru"

    han = len(_RE_HAN.findall(s))
    cyr = len(_RE_CYRILLIC.findall(s))
    lat = len(_RE_LATIN.findall(s))

    # Prefer Chinese if any Han characters are present.
    if han > 0:
        return "zh"

    # If it's mostly Cyrillic -> Russian.
    if cyr >= max(lat, 1):
        return "ru"

    # Otherwise default to English.
    return "en"

