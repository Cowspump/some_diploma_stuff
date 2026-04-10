import logging
from typing import Any

from sqlalchemy.orm import Session

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database  # noqa: E402
import models  # noqa: E402
from api.translation import translate_hybrid  # noqa: E402

logger = logging.getLogger(__name__)

SUPPORTED_TARGET_LANGS = ("en", "zh")
SUPPORTED_LANGS_ALL = ("ru", "en", "zh")


def _upsert_test_translation(db: Session, *, test_id: int, lang: str, title: str, description: str | None) -> None:
    existing = (
        db.query(models.TestTranslation)
        .filter(models.TestTranslation.test_id == test_id, models.TestTranslation.lang == lang)
        .first()
    )
    if existing:
        existing.translated_title = title
        existing.translated_description = description
        return
    db.add(
        models.TestTranslation(
            test_id=test_id,
            lang=lang,
            translated_title=title,
            translated_description=description,
        )
    )


def _upsert_question_translation(db: Session, *, question_id: int, lang: str, text: str, options: list[dict[str, Any]]) -> None:
    existing = (
        db.query(models.QuestionTranslation)
        .filter(models.QuestionTranslation.question_id == question_id, models.QuestionTranslation.lang == lang)
        .first()
    )
    if existing:
        existing.translated_text = text
        existing.translated_options = options
        return
    db.add(
        models.QuestionTranslation(
            question_id=question_id,
            lang=lang,
            translated_text=text,
            translated_options=options,
        )
    )


def translate_test_task(test_id: int, *, auto_install_models: bool = False) -> None:
    """
    Background task: translate Test title/description source_lang->(other langs) into TestTranslation.
    """
    db = database.SessionLocal()
    try:
        test = db.query(models.Test).filter(models.Test.id == test_id).first()
        if not test:
            return

        base_title = (test.title or "").strip()
        base_desc = (test.description or "").strip() if test.description else None
        if not base_title:
            return

        source_lang = (getattr(test, "source_lang", None) or "ru").strip().lower() or "ru"
        if source_lang not in SUPPORTED_LANGS_ALL:
            source_lang = "ru"
        targets = [l for l in SUPPORTED_LANGS_ALL if l != source_lang]

        changed = False
        for lang in targets:
            t_title = translate_hybrid(base_title, from_lang=source_lang, to_lang=lang, auto_install_models=auto_install_models)
            t_desc = translate_hybrid(base_desc, from_lang=source_lang, to_lang=lang, auto_install_models=auto_install_models) if base_desc else ""
            if t_title is None:
                continue

            _upsert_test_translation(
                db,
                test_id=test.id,
                lang=lang,
                title=t_title.strip(),
                description=(t_desc.strip() if isinstance(t_desc, str) else None) or None,
            )
            changed = True

        if changed:
            db.commit()
    except Exception as e:
        logger.warning("translate_test_task failed test_id=%s: %s", test_id, e, exc_info=True)
        db.rollback()
    finally:
        db.close()


def _upsert_material_translation(db: Session, *, material_id: int, lang: str, title: str, content: str) -> None:
    existing = (
        db.query(models.MaterialTranslation)
        .filter(models.MaterialTranslation.material_id == material_id, models.MaterialTranslation.lang == lang)
        .first()
    )
    if existing:
        existing.translated_title = title
        existing.translated_content = content
        return
    db.add(
        models.MaterialTranslation(
            material_id=material_id,
            lang=lang,
            translated_title=title,
            translated_content=content,
        )
    )


def _upsert_journal_translation(db: Session, *, journal_id: int, lang: str, note_text: str) -> None:
    existing = (
        db.query(models.JournalTranslation)
        .filter(models.JournalTranslation.journal_id == journal_id, models.JournalTranslation.lang == lang)
        .first()
    )
    if existing:
        existing.translated_note_text = note_text
        return
    db.add(
        models.JournalTranslation(
            journal_id=journal_id,
            lang=lang,
            translated_note_text=note_text,
        )
    )


def translate_journal_task(journal_id: int, *, auto_install_models: bool = False) -> None:
    """
    Background task: translate Journal note_text source_lang->(other langs) into JournalTranslation.
    """
    db = database.SessionLocal()
    try:
        j = db.query(models.Journal).filter(models.Journal.id == journal_id).first()
        if not j:
            return

        base_note = (j.note_text or "").strip()
        if not base_note:
            return

        source_lang = (getattr(j, "source_lang", None) or "ru").strip().lower() or "ru"
        if source_lang not in SUPPORTED_LANGS_ALL:
            source_lang = "ru"

        targets = [l for l in SUPPORTED_LANGS_ALL if l != source_lang]

        changed = False
        for lang in targets:
            t_note = translate_hybrid(base_note, from_lang=source_lang, to_lang=lang, auto_install_models=auto_install_models)
            if not isinstance(t_note, str) or not t_note.strip():
                continue
            _upsert_journal_translation(db, journal_id=j.id, lang=lang, note_text=t_note.strip())
            changed = True

        if changed:
            db.commit()
    except Exception as e:
        logger.warning("translate_journal_task failed journal_id=%s: %s", journal_id, e, exc_info=True)
        db.rollback()
    finally:
        db.close()


def translate_material_task(material_id: int, *, auto_install_models: bool = False) -> None:
    db = database.SessionLocal()
    try:
        m = db.query(models.Material).filter(models.Material.id == material_id).first()
        if not m:
            return

        base_title = (m.title or "").strip()
        base_content = (m.content or "").strip()
        if not base_title:
            return

        source_lang = (getattr(m, "source_lang", None) or "ru").strip().lower() or "ru"
        if source_lang not in SUPPORTED_LANGS_ALL:
            source_lang = "ru"

        targets = [l for l in SUPPORTED_LANGS_ALL if l != source_lang]

        changed = False
        for lang in targets:
            t_title = translate_hybrid(base_title, from_lang=source_lang, to_lang=lang, auto_install_models=auto_install_models)
            t_content = translate_hybrid(base_content, from_lang=source_lang, to_lang=lang, auto_install_models=auto_install_models) if base_content else ""
            if t_title is None:
                continue

            _upsert_material_translation(
                db,
                material_id=m.id,
                lang=lang,
                title=t_title.strip(),
                content=(t_content.strip() if isinstance(t_content, str) else "") or "",
            )
            changed = True

        if changed:
            db.commit()
    except Exception as e:
        logger.warning("translate_material_task failed material_id=%s: %s", material_id, e, exc_info=True)
        db.rollback()
    finally:
        db.close()


def translate_question_task(question_id: int, *, auto_install_models: bool = False) -> None:
    """
    Background task: translate Question text/options source_lang->(other langs) into QuestionTranslation.
    """
    db = database.SessionLocal()
    try:
        q = db.query(models.Question).filter(models.Question.id == question_id).first()
        if not q:
            return

        base_text = (q.text or "").strip()
        base_options = q.options or []
        if not base_text or not isinstance(base_options, list):
            return

        source_lang = (getattr(q, "source_lang", None) or "ru").strip().lower() or "ru"
        if source_lang not in SUPPORTED_LANGS_ALL:
            source_lang = "ru"
        targets = [l for l in SUPPORTED_LANGS_ALL if l != source_lang]

        changed = False
        for lang in targets:
            t_text = translate_hybrid(base_text, from_lang=source_lang, to_lang=lang, auto_install_models=auto_install_models)
            if t_text is None:
                continue

            t_options: list[dict[str, Any]] = []
            ok_all = True
            for opt in base_options:
                opt_text = (opt or {}).get("text") if isinstance(opt, dict) else None
                opt_points = (opt or {}).get("points") if isinstance(opt, dict) else None
                if not isinstance(opt_text, str):
                    ok_all = False
                    break
                translated_opt = translate_hybrid(opt_text, from_lang=source_lang, to_lang=lang, auto_install_models=auto_install_models)
                if translated_opt is None:
                    ok_all = False
                    break
                t_options.append({"text": translated_opt.strip(), "points": int(opt_points or 0)})

            if not ok_all:
                continue

            _upsert_question_translation(
                db,
                question_id=q.id,
                lang=lang,
                text=t_text.strip(),
                options=t_options,
            )
            changed = True

        if changed:
            db.commit()
    except Exception as e:
        logger.warning("translate_question_task failed question_id=%s: %s", question_id, e, exc_info=True)
        db.rollback()
    finally:
        db.close()

