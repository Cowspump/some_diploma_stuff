import logging
from typing import Optional

logger = logging.getLogger(__name__)

PIVOT_ROUTES = {
    ("ru", "zh"): ["en"],
    ("zh", "ru"): ["en"],
}


def _normalize_lang(lang: str) -> str:
    lang = (lang or "").strip().lower()
    if lang in ("ru", "en", "zh"):
        return lang
    return "ru"


def _ensure_package(from_lang: str, to_lang: str, *, auto_install: bool) -> bool:
    try:
        import argostranslate.package  # type: ignore

        installed = argostranslate.package.get_installed_packages()
        for p in installed:
            if getattr(p, "from_code", None) == from_lang and getattr(p, "to_code", None) == to_lang:
                return True

        if not auto_install:
            return False

        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = None
        for p in available:
            if getattr(p, "from_code", None) == from_lang and getattr(p, "to_code", None) == to_lang:
                pkg = p
                break
        if not pkg:
            return False

        path = pkg.download()
        argostranslate.package.install_from_path(path)
        return True
    except Exception as e:
        logger.warning("Argos package ensure failed %s->%s: %s", from_lang, to_lang, e)
        return False


def _translate_direct(text: str, from_lang: str, to_lang: str) -> Optional[str]:
    import argostranslate.translate  # type: ignore
    return argostranslate.translate.translate(text, from_lang, to_lang)


def translate(text: str, *, from_lang: str = "ru", to_lang: str = "en", auto_install: bool = False) -> Optional[str]:
    try:
        text = text or ""
        if not text.strip():
            return ""

        from_lang = _normalize_lang(from_lang)
        to_lang = _normalize_lang(to_lang)
        if from_lang == to_lang:
            return text

        # Try direct translation first
        if _ensure_package(from_lang, to_lang, auto_install=auto_install):
            return _translate_direct(text, from_lang, to_lang)

        # Try pivot translation (e.g. ru -> en -> zh)
        pivots = PIVOT_ROUTES.get((from_lang, to_lang))
        if pivots:
            result = text
            chain = [from_lang] + pivots + [to_lang]
            for i in range(len(chain) - 1):
                src, dst = chain[i], chain[i + 1]
                if not _ensure_package(src, dst, auto_install=auto_install):
                    logger.warning("Pivot package not available: %s->%s", src, dst)
                    return None
                result = _translate_direct(result, src, dst)
                if result is None:
                    return None
            return result

        return None
    except Exception as e:
        logger.warning("Argos translate failed %s->%s: %s", from_lang, to_lang, e)
        return None

