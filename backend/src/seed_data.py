"""
Auto-seed: populates the database with test data if it's empty.
Called from main.py on startup.
"""
import logging
import random
import models
import auth
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import re
from datetime import date

logger = logging.getLogger(__name__)

THERAPIST = {"full_name": "Dr. Anna Petrova", "mail": "anna.petrova@gmail.com", "password": "password123", "role": "therapist"}
WORKERS = [
    {"full_name": "Иван Сидоров", "mail": "ivan.sidorov@gmail.com", "password": "password123", "role": "worker"},
    {"full_name": "Maria Chen", "mail": "maria.chen@gmail.com", "password": "password123", "role": "worker"},
    {"full_name": "Алексей Козлов", "mail": "alexey.kozlov@gmail.com", "password": "password123", "role": "worker"},
    {"full_name": "Li Wei", "mail": "li.wei@gmail.com", "password": "password123", "role": "worker"},
    {"full_name": "Wang Xiaoming", "mail": "wang.xiaoming@gmail.com", "password": "password123", "role": "worker"},
    {"full_name": "Zhang Wei", "mail": "zhang.wei@gmail.com", "password": "password123", "role": "worker"},
    {"full_name": "Liu Xinyi", "mail": "liu.xinyi@gmail.com", "password": "password123", "role": "worker"},
]

def _extract_title(line: str) -> str | None:
    s = (line or "").strip()
    if not s:
        return None
    lowered = s.casefold()

    # Variants observed in files:
    # - "Название 职业倦怠评估量表"
    # - "Название: 抑郁状态评估量表"
    # - "НАЗВАНИЕ :焦虑状态评估量表"
    # - "1) Название: Шкала ..."
    # - "1) НазВание: ..."
    # - "1)Название: ..."
    if "название" in lowered or lowered.startswith("title"):
        # strip optional leading numbering like "1)" / "1." and leading "Название"/"Title"
        s_norm = re.sub(r"^\s*\d+\s*[\)\.]\s*", "", s)
        s2 = re.sub(r"^(название|title)\s*[:：]?\s*", "", s_norm, flags=re.IGNORECASE)
        s2 = s2.strip()
        return s2 or None

    return None


def _parse_option_line(line: str) -> dict | None:
    s = (line or "").strip()
    if not s:
        return None

    # Generic: A. text (0 баллов) / (1 минута) / (0 points) / （0分） / (на 1 пункт)
    m = re.match(r"^[A-D]\.\s*(.+?)\s*[（(]\s*(?:на\s*)?(\d+)\s*[^)）]*[)）]\s*$", s, flags=re.IGNORECASE)
    if m:
        return {"text": m.group(1).strip(), "points": int(m.group(2))}

    # A. text（0分） / A. text (0分)
    m = re.match(r"^[A-D]\.\s*(.+?)\s*[（(]\s*(\d+)\s*分\s*[)）]\s*$", s)
    if m:
        return {"text": m.group(1).strip(), "points": int(m.group(2))}

    # A. text (0) / A. text（0）
    m = re.match(r"^[A-D]\.\s*(.+?)\s*[（(]\s*(\d+)\s*[)）]\s*$", s)
    if m:
        return {"text": m.group(1).strip(), "points": int(m.group(2))}

    # A. text (0 points)
    m = re.match(r"^[A-D]\.\s*(.+?)\s*[（(]\s*(\d+)\s*points?\s*[)）]\s*$", s, flags=re.IGNORECASE)
    if m:
        return {"text": m.group(1).strip(), "points": int(m.group(2))}

    # A. text → 0
    m = re.match(r"^[A-D]\.\s*(.+?)\s*→\s*(\d+)\s*$", s)
    if m:
        return {"text": m.group(1).strip(), "points": int(m.group(2))}

    return None


def _needs_test_reseed(db: Session) -> bool:
    """
    Reseed tests when we detect that canonical RU content didn't get loaded
    (e.g. tests ended up in ZH due to parsing issues) or when forced via env.
    """
    if os.getenv("FORCE_RESEED_TESTS") == "1":
        return True

    # No tests => if users already exist, we still need to seed tests
    any_test = db.query(models.Test).first()
    if not any_test:
        return True

    # If any canonical test title contains CJK, likely RU parsing didn't apply
    def has_cjk(text: str | None) -> bool:
        if not text:
            return False
        return any("\u4e00" <= ch <= "\u9fff" for ch in text)

    tests = db.query(models.Test).all()
    if any(has_cjk(t.title) or has_cjk(t.description) for t in tests):
        return True

    # Sometimes titles are RU but canonical questions are still ZH due to parsing issues.
    questions = db.query(models.Question).limit(50).all()
    return any(has_cjk(q.text) for q in questions)


def _needs_materials_reseed(db: Session) -> bool:
    """
    Reseed materials when we detect that canonical RU content didn't get loaded
    (e.g. materials ended up in ZH due to parsing issues) or when forced via env.
    """
    if os.getenv("FORCE_RESEED_MATERIALS") == "1":
        return True

    any_material = db.query(models.Material).first()
    if not any_material:
        return True

    def has_cjk(text: str | None) -> bool:
        if not text:
            return False
        return any("\u4e00" <= ch <= "\u9fff" for ch in text)

    mats = db.query(models.Material).limit(25).all()
    return any(has_cjk(m.title) or has_cjk(m.content) for m in mats)


def _reseed_tests_from_txt(db: Session, therapist_id: int):
    """
    Drop existing tests/questions/translations/results and re-create them from txt files.
    Users/journals are preserved.
    """
    logger.info("Reseeding tests from backend/tests/*.txt ...")

    # Delete dependent rows first (FK order)
    db.query(models.QuestionTranslation).delete(synchronize_session=False)
    db.query(models.TestTranslation).delete(synchronize_session=False)
    db.query(models.TestResult).delete(synchronize_session=False)
    db.query(models.Question).delete(synchronize_session=False)
    db.query(models.Test).delete(synchronize_session=False)
    db.flush()

    all_tests = []
    for test_data in (_load_tests_from_txt() or []):
        # Canonical language in DB: RU. Translations for ZH/EN go into *_translations tables.
        has_ru = bool((test_data.get("title_ru") or "").strip() or (test_data.get("description_ru") or "").strip())
        canonical_lang = "ru" if has_ru else ("en" if (test_data.get("title_en") or "").strip() else "zh")
        test = models.Test(
            title=test_data.get("title_ru") or test_data.get("title_zh") or test_data.get("title_en"),
            description=test_data.get("description_ru") or test_data.get("description_zh") or test_data.get("description_en"),
            therapist_id=therapist_id,
            source_lang=canonical_lang,
        )
        db.add(test)
        db.flush()
        all_tests.append(test)

        for lang, title_key, desc_key in (
            ("zh", "title_zh", "description_zh"),
            ("en", "title_en", "description_en"),
        ):
            title_val = test_data.get(title_key)
            if title_val:
                db.add(models.TestTranslation(
                    test_id=test.id,
                    lang=lang,
                    translated_title=title_val,
                    translated_description=test_data.get(desc_key),
                ))

        for q_data in test_data["questions"]:
            base_text = q_data.get("text_ru") or q_data.get("text_zh") or q_data.get("text_en")
            base_options = q_data.get("options_ru") or q_data.get("options_zh") or q_data.get("options_en")
            q_has_ru = bool((q_data.get("text_ru") or "").strip())
            q_canonical_lang = "ru" if q_has_ru else ("en" if (q_data.get("text_en") or "").strip() else "zh")
            question = models.Question(text=base_text, options=base_options, test_id=test.id, source_lang=q_canonical_lang)
            db.add(question)
            db.flush()

            for lang, text_key, options_key in (
                ("zh", "text_zh", "options_zh"),
                ("en", "text_en", "options_en"),
            ):
                t_text = q_data.get(text_key)
                t_opts = q_data.get(options_key)
                if t_text and t_opts:
                    db.add(models.QuestionTranslation(
                        question_id=question.id,
                        lang=lang,
                        translated_text=t_text,
                        translated_options=t_opts,
                    ))

    db.commit()
    logger.info("Tests reseeded successfully (%s tests).", len(all_tests))


def _reseed_materials_from_txt(db: Session, author_id: int):
    """
    Drop existing materials/translations and re-create them from txt files.
    Users/journals/tests are preserved.
    """
    logger.info("Reseeding materials from backend/materials/*.txt ...")

    db.query(models.MaterialTranslation).delete(synchronize_session=False)
    db.query(models.Material).delete(synchronize_session=False)
    db.flush()

    materials = _load_materials_from_txt() or []
    for m in materials:
        base_title = m.get("title_ru") or m.get("title_zh") or m.get("title_en")
        base_content = m.get("content_ru") or m.get("content_zh") or m.get("content_en")
        emoji = (m.get("emoji") or "").strip() or None
        if not base_title or not base_content:
            continue

        has_ru = bool((m.get("title_ru") or "").strip() or (m.get("content_ru") or "").strip())
        canonical_lang = "ru" if has_ru else ("en" if (m.get("title_en") or "").strip() else "zh")
        mat = models.Material(
            title=base_title,
            content=base_content,
            emoji=emoji,
            author_id=author_id,
            source_lang=canonical_lang,
        )
        db.add(mat)
        db.flush()

        for lang, title_key, content_key in (
            ("zh", "title_zh", "content_zh"),
            ("en", "title_en", "content_en"),
        ):
            t_title = m.get(title_key)
            t_content = m.get(content_key)
            if t_title and t_content:
                db.add(
                    models.MaterialTranslation(
                        material_id=mat.id,
                        lang=lang,
                        translated_title=t_title,
                        translated_content=t_content,
                    )
                )

    db.commit()
    logger.info("Materials reseeded successfully (%s materials).", len(materials))


def _load_tests_from_txt() -> list[dict]:
    """
    Load tests from backend/tests/{zh_tests,rus_tests,en_tests}.txt.

    Strategy:
    - Parse each language file with the same parser.
    - Merge by test/question/option index (files must have the same structure/order).
    """

    def read_lines(name: str) -> list[str] | None:
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", name))
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return [ln.rstrip("\n") for ln in f]

    zh_lines = read_lines(os.path.join("tests", "zh_tests.txt"))
    if not zh_lines:
        logger.warning("Seed tests file not found: backend/tests/zh_tests.txt")
        return []

    ru_lines = read_lines(os.path.join("tests", "rus_tests.txt"))
    en_lines = read_lines(os.path.join("tests", "en_tests.txt"))

    def parse(lines: list[str]) -> list[dict]:
        tests: list[dict] = []
        current_test: dict | None = None
        current_question_text: str | None = None
        current_options: list[dict] = []

        def flush_question():
            nonlocal current_question_text, current_options, current_test
            if not current_test:
                current_question_text = None
                current_options = []
                return
            if current_question_text and len(current_options) >= 2:
                q_text = current_question_text.strip()
                current_test["questions"].append(
                    {
                        "text": q_text,
                        "options": current_options,
                    }
                )
            current_question_text = None
            current_options = []

        def flush_test():
            nonlocal current_test
            if current_test and current_test.get("questions"):
                tests.append(current_test)
            current_test = None

        for raw in lines:
            line = (raw or "").strip()
            title = _extract_title(line)
            if title:
                flush_question()
                flush_test()
                current_test = {
                    "title": title,
                    "description": None,
                    "questions": [],
                }
                continue

            if not current_test:
                continue

            if line == "⸻":
                flush_question()
                continue

            opt = _parse_option_line(line)
            if opt:
                current_options.append(opt)
                continue

            # numbering like "1. 紧张感"
            if re.match(r"^\d+\.\s*", line):
                flush_question()
                current_question_text = re.sub(r"^\d+\.\s*", "", line).strip()
                continue

            if not line:
                continue

            if (
                not current_test.get("questions")
                and current_question_text is None
                and not current_options
                and current_test.get("description") is None
            ):
                current_test["description"] = line
                continue

            if current_question_text:
                current_question_text = f"{current_question_text} {line}".strip()
            else:
                flush_question()
                current_question_text = line

        flush_question()
        flush_test()
        return tests

    zh_tests = parse(zh_lines)
    ru_tests: list[dict] = parse(ru_lines) if ru_lines else []
    en_tests: list[dict] = parse(en_lines) if en_lines else []

    # Merge by index
    merged: list[dict] = []
    for ti, zt in enumerate(zh_tests):
        rt = ru_tests[ti] if ti < len(ru_tests) else None
        et = en_tests[ti] if ti < len(en_tests) else None

        out = {
            "title_zh": zt["title"],
            "title_ru": (rt["title"] if rt else zt["title"]),
            "title_en": (et["title"] if et else zt["title"]),
            "description_zh": zt.get("description"),
            "description_ru": (rt.get("description") if rt else zt.get("description")),
            "description_en": (et.get("description") if et else zt.get("description")),
            "questions": [],
        }

        zqs = zt.get("questions") or []
        rqs = (rt.get("questions") if rt else None) or []
        eqs = (et.get("questions") if et else None) or []

        for qi, zq in enumerate(zqs):
            rq = rqs[qi] if qi < len(rqs) else None
            eq = eqs[qi] if qi < len(eqs) else None

            zo = zq.get("options") or []
            ro = (rq.get("options") if rq else None) or []
            eo = (eq.get("options") if eq else None) or []

            # Ensure points come from ZH (canonical)
            merged_ru_opts = []
            merged_en_opts = []
            for oi, zopt in enumerate(zo):
                rtext = ro[oi]["text"] if oi < len(ro) else zopt["text"]
                etext = eo[oi]["text"] if oi < len(eo) else zopt["text"]
                merged_ru_opts.append({"text": rtext, "points": zopt["points"]})
                merged_en_opts.append({"text": etext, "points": zopt["points"]})

            out["questions"].append(
                {
                    "text_zh": zq.get("text"),
                    "text_ru": (rq.get("text") if rq else zq.get("text")),
                    "text_en": (eq.get("text") if eq else zq.get("text")),
                    "options_zh": zo,
                    "options_ru": merged_ru_opts,
                    "options_en": merged_en_opts,
                }
            )

        merged.append(out)

    return merged


def _load_materials_from_txt() -> list[dict]:
    """
    Load materials from backend/materials/{zh_mat,rus_mat,eng_mat}.txt

    Strategy:
    - Parse each language file with the same parser.
    - Merge by material index (files must have the same structure/order).
    """

    def read_lines(rel_path: str) -> list[str] | None:
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel_path))
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return [ln.rstrip("\n") for ln in f]

    zh_lines = read_lines(os.path.join("materials", "zh_mat.txt"))
    ru_lines = read_lines(os.path.join("materials", "rus_mat.txt"))
    en_lines = read_lines(os.path.join("materials", "eng_mat.txt"))

    if not (zh_lines and ru_lines and en_lines):
        logger.warning("Seed materials files not found under backend/materials/")
        return []

    def parse(lines: list[str]) -> list[dict]:
        items: list[dict] = []
        current_title: str | None = None
        current_lines: list[str] = []
        current_emoji: str | None = None
        in_text = False

        title_re = re.compile(r"^\s*\d+\.\s*НАЗВАНИЕ\s*[:：]\s*(.+?)\s*$", flags=re.IGNORECASE)

        def flush():
            nonlocal current_title, current_lines, in_text, current_emoji
            if current_title and current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    items.append({"title": current_title.strip(), "content": content, "emoji": current_emoji})
            current_title = None
            current_lines = []
            current_emoji = None
            in_text = False

        for raw in lines:
            line = (raw or "").rstrip("\n")
            s = line.strip()

            m = title_re.match(line)
            if m:
                flush()
                current_title = m.group(1).strip()
                continue

            if current_title is None:
                continue

            lowered = s.casefold()
            if lowered.startswith("текст"):
                in_text = True
                continue

            if lowered.startswith("смайлик"):
                # e.g. "СМАЙЛИК: 🥱"
                m_emoji = re.search(r"[:：]\s*(.+)\s*$", line)
                if m_emoji:
                    current_emoji = m_emoji.group(1).strip() or None
                continue

            if not in_text:
                continue

            current_lines.append(line)

        flush()
        return items

    zh_items = parse(zh_lines)
    ru_items = parse(ru_lines)
    en_items = parse(en_lines)

    merged: list[dict] = []
    max_len = max(len(zh_items), len(ru_items), len(en_items))
    for i in range(max_len):
        z = zh_items[i] if i < len(zh_items) else None
        r = ru_items[i] if i < len(ru_items) else None
        e = en_items[i] if i < len(en_items) else None

        if not (z or r or e):
            continue

        merged.append(
            {
                "title_zh": (z.get("title") if z else None),
                "content_zh": (z.get("content") if z else None),
                "title_ru": (r.get("title") if r else (z.get("title") if z else None)),
                "content_ru": (r.get("content") if r else (z.get("content") if z else None)),
                "title_en": (e.get("title") if e else (z.get("title") if z else None)),
                "content_en": (e.get("content") if e else (z.get("content") if z else None)),
                "emoji": (r.get("emoji") if r else (z.get("emoji") if z else (e.get("emoji") if e else None))),
            }
        )

    return merged

"""
LEGACY (disabled): previous long multi-language seed.
Kept temporarily to preserve history, but not executed/parsed as Python code.

TESTS = [
    {
        "title_ru": "Оценка профессионального выгорания",
        "title_zh": "职业倦怠评估量表",
        "title_en": "Burnout Assessment Scale",
        "description_ru": "Оцените уровень профессионального выгорания по вашему состоянию в последнее время.",
        "description_zh": "请根据你最近一段时间的工作或学习状态，评估职业倦怠程度",
        "description_en": "Assess your level of burnout based on your recent work/study experience.",
        "questions": [
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (эмоциональное истощение).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（情绪耗竭）：",
             "text_en": "Choose the option that best matches you (emotional exhaustion).",
             "options_ru": [
                 {"text": "Я долго чувствую эмоциональное истощение почти каждый день", "points": 0},
                 {"text": "Я часто чувствую эмоциональную усталость", "points": 1},
                 {"text": "Иногда я чувствую усталость", "points": 2},
                 {"text": "Я чувствую себя энергично", "points": 3},
             ],
             "options_zh": [
                {"text": "我长期感到情绪被完全耗尽，几乎每天如此", "points": 0}, {"text": "我经常感到情绪疲惫", "points": 1},
                {"text": "我有时会感到疲劳", "points": 2}, {"text": "我精力充沛", "points": 3}]},
             "options_en": [
                 {"text": "I feel emotionally drained almost every day", "points": 0},
                 {"text": "I often feel emotionally tired", "points": 1},
                 {"text": "I sometimes feel tired", "points": 2},
                 {"text": "I feel energetic", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (усталость от работы).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作疲劳）：",
             "text_en": "Choose the option that best matches you (work fatigue).",
             "options_ru": [
                 {"text": "Работа каждый день делает меня крайне уставшим", "points": 0},
                 {"text": "После работы я часто очень устаю", "points": 1},
                 {"text": "Иногда я устаю", "points": 2},
                 {"text": "После работы я чувствую себя нормально", "points": 3},
             ],
             "options_zh": [
                {"text": "每天工作都会让我感到极度疲惫", "points": 0}, {"text": "工作后经常感到很累", "points": 1},
                {"text": "有时感到疲劳", "points": 2}, {"text": "工作后状态良好", "points": 3}]},
             "options_en": [
                 {"text": "Work leaves me extremely exhausted every day", "points": 0},
                 {"text": "I often feel very tired after work", "points": 1},
                 {"text": "I sometimes feel tired", "points": 2},
                 {"text": "I feel okay after work", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (стресс от работы).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作压力）：",
             "text_en": "Choose the option that best matches you (work stress).",
             "options_ru": [
                 {"text": "Мысли о работе вызывают сильный стресс и отторжение", "points": 0},
                 {"text": "Я часто чувствую заметный стресс из‑за работы", "points": 1},
                 {"text": "Есть стресс, но я справляюсь", "points": 2},
                 {"text": "Я легко справляюсь с рабочими задачами", "points": 3},
             ],
             "options_zh": [
                {"text": "我一想到工作就感到强烈压力甚至抗拒", "points": 0}, {"text": "我经常对工作感到明显压力", "points": 1},
                {"text": "我有一定压力，但可以应对", "points": 2}, {"text": "我可以轻松面对工作", "points": 3}]},
             "options_en": [
                 {"text": "Thinking about work causes strong stress and resistance", "points": 0},
                 {"text": "I often feel noticeable work-related stress", "points": 1},
                 {"text": "I feel some stress but can cope", "points": 2},
                 {"text": "I can handle work easily", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (нагрузка).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作负担）：",
             "text_en": "Choose the option that best matches you (workload).",
             "options_ru": [
                 {"text": "Я больше не выдерживаю текущую нагрузку", "points": 0},
                 {"text": "Нагрузка кажется тяжёлой", "points": 1},
                 {"text": "Нагрузка в целом приемлемая", "points": 2},
                 {"text": "Нагрузка нормальная", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己已经无法承受当前的工作负担", "points": 0}, {"text": "我感觉工作负担较重", "points": 1},
                {"text": "工作负担尚可接受", "points": 2}, {"text": "工作负担正常", "points": 3}]},
             "options_en": [
                 {"text": "I can no longer handle my current workload", "points": 0},
                 {"text": "My workload feels heavy", "points": 1},
                 {"text": "My workload is generally manageable", "points": 2},
                 {"text": "My workload is normal", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (восстановление эмоций).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（情绪恢复）：",
             "text_en": "Choose the option that best matches you (emotional recovery).",
             "options_ru": [
                 {"text": "Я эмоционально опустошён(а) и не могу восстановиться", "points": 0},
                 {"text": "Я часто чувствую упадок настроения", "points": 1},
                 {"text": "Иногда у меня бывает такое", "points": 2},
                 {"text": "Моё настроение в целом стабильное", "points": 3},
             ],
             "options_zh": [
                {"text": "我感到情绪被完全掏空，难以恢复", "points": 0}, {"text": "我经常感到情绪低落", "points": 1},
                {"text": "偶尔有这种感觉", "points": 2}, {"text": "情绪基本稳定", "points": 3}]},
             "options_en": [
                 {"text": "I feel emotionally empty and struggle to recover", "points": 0},
                 {"text": "I often feel low emotionally", "points": 1},
                 {"text": "I sometimes feel this way", "points": 2},
                 {"text": "My mood is generally stable", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (уровень энергии).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（精力状况）：",
             "text_en": "Choose the option that best matches you (energy level).",
             "options_ru": [
                 {"text": "На работе я полностью вымотан(а)", "points": 0},
                 {"text": "Мне часто не хватает энергии", "points": 1},
                 {"text": "Иногда я чувствую усталость", "points": 2},
                 {"text": "У меня достаточно энергии", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己在工作中已经精疲力尽", "points": 0}, {"text": "经常感到精力不足", "points": 1},
                {"text": "偶尔疲惫", "points": 2}, {"text": "精力充足", "points": 3}]},
             "options_en": [
                 {"text": "I feel completely worn out at work", "points": 0},
                 {"text": "I often lack energy", "points": 1},
                 {"text": "I sometimes feel tired", "points": 2},
                 {"text": "I have plenty of energy", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (интерес к работе).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作兴趣）：",
             "text_en": "Choose the option that best matches you (interest in work).",
             "options_ru": [
                 {"text": "Я крайне устал(а) и испытываю отторжение к работе", "points": 0},
                 {"text": "Я заметно устаю и теряю интерес", "points": 1},
                 {"text": "Иногда мне становится скучно/тяжело", "points": 2},
                 {"text": "Я сохраняю интерес к работе", "points": 3},
             ],
             "options_zh": [
                {"text": "我对工作感到极度厌倦甚至抗拒", "points": 0}, {"text": "我对工作有明显厌倦感", "points": 1},
                {"text": "偶尔会感到厌倦", "points": 2}, {"text": "我对工作仍然保持兴趣", "points": 3}]},
             "options_en": [
                 {"text": "I feel extremely burnt out and resistant to work", "points": 0},
                 {"text": "I often feel bored/tired and lose interest", "points": 1},
                 {"text": "I sometimes feel bored or overwhelmed", "points": 2},
                 {"text": "I still feel interested in my work", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (начало работы).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（开始工作）：",
             "text_en": "Choose the option that best matches you (starting work).",
             "options_ru": [
                 {"text": "Каждый день начать работу очень трудно", "points": 0},
                 {"text": "Я часто откладываю и не хочу начинать", "points": 1},
                 {"text": "Иногда я прокрастинирую", "points": 2},
                 {"text": "Обычно я начинаю без проблем", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得每天开始工作都非常困难", "points": 0}, {"text": "我经常拖延或不想开始工作", "points": 1},
                {"text": "有时会拖延", "points": 2}, {"text": "我可以正常开始工作", "points": 3}]},
             "options_en": [
                 {"text": "Starting work each day is very difficult", "points": 0},
                 {"text": "I often procrastinate or avoid starting", "points": 1},
                 {"text": "I sometimes procrastinate", "points": 2},
                 {"text": "I can start work normally", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (эмоции от работы).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作情绪）：",
             "text_en": "Choose the option that best matches you (work emotions).",
             "options_ru": [
                 {"text": "Работа вызывает эмоциональный срыв или ощущение, что я не справляюсь", "points": 0},
                 {"text": "Работа вызывает сильный стресс", "points": 1},
                 {"text": "Есть умеренный стресс", "points": 2},
                 {"text": "Стресс контролируемый", "points": 3},
             ],
             "options_zh": [
                {"text": "工作让我感到情绪崩溃或难以承受", "points": 0}, {"text": "工作让我压力很大", "points": 1},
                {"text": "有一定压力", "points": 2}, {"text": "工作压力在可控范围内", "points": 3}]},
             "options_en": [
                 {"text": "Work makes me feel emotionally overwhelmed", "points": 0},
                 {"text": "Work causes a lot of stress", "points": 1},
                 {"text": "I feel some stress", "points": 2},
                 {"text": "My work stress is manageable", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (отношение к людям).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（对他人态度）：",
             "text_en": "Choose the option that best matches you (attitude toward others).",
             "options_ru": [
                 {"text": "Я стал(а) холодным(ой) и безразличным(ой) к людям", "points": 0},
                 {"text": "Иногда я раздражаюсь на людей", "points": 1},
                 {"text": "Иногда я бываю отстранён(а)", "points": 2},
                 {"text": "Я сохраняю нормальное отношение к людям", "points": 3},
             ],
             "options_zh": [
                {"text": "我对他人变得冷漠甚至无感", "points": 0}, {"text": "我有时对他人不耐烦", "points": 1},
                {"text": "偶尔表现出冷淡", "points": 2}, {"text": "我对他人保持正常态度", "points": 3}]},
             "options_en": [
                 {"text": "I’ve become cold or indifferent toward others", "points": 0},
                 {"text": "I sometimes feel impatient with people", "points": 1},
                 {"text": "I can be distant at times", "points": 2},
                 {"text": "I keep a normal attitude toward others", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (забота о других).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（关心他人）：",
             "text_en": "Choose the option that best matches you (caring about others).",
             "options_ru": [
                 {"text": "Меня совсем не заботят проблемы других", "points": 0},
                 {"text": "Мне сложно заботиться о других", "points": 1},
                 {"text": "Иногда я отдаляюсь", "points": 2},
                 {"text": "Я стараюсь понимать и поддерживать других", "points": 3},
             ],
             "options_zh": [
                {"text": "我对他人的问题完全不关心", "points": 0}, {"text": "我不太愿意关心他人", "points": 1},
                {"text": "有时会疏远他人", "points": 2}, {"text": "我愿意理解和关心他人", "points": 3}]},
             "options_en": [
                 {"text": "I don't care about other people's problems", "points": 0},
                 {"text": "I find it hard to care about others", "points": 1},
                 {"text": "I distance myself sometimes", "points": 2},
                 {"text": "I try to understand and care about others", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (уважение к другим).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（尊重他人）：",
             "text_en": "Choose the option that best matches you (respect for others).",
             "options_ru": [
                 {"text": "Я воспринимаю людей как “объекты задач”, а не как людей", "points": 0},
                 {"text": "Иногда я так думаю", "points": 1},
                 {"text": "Редко, но бывает", "points": 2},
                 {"text": "Я стараюсь уважать людей", "points": 3},
             ],
             "options_zh": [
                {"text": "我把他人当作任务对象而不是人", "points": 0}, {"text": "有时会这样看待他人", "points": 1},
                {"text": "偶尔出现这种情况", "points": 2}, {"text": "我始终尊重他人", "points": 3}]},
             "options_en": [
                 {"text": "I treat people like tasks rather than individuals", "points": 0},
                 {"text": "I sometimes think this way", "points": 1},
                 {"text": "It happens occasionally", "points": 2},
                 {"text": "I always try to respect people", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (терпение).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（耐心程度）：",
             "text_en": "Choose the option that best matches you (patience).",
             "options_ru": [
                 {"text": "Мне явно не хватает терпения с людьми", "points": 0},
                 {"text": "Я легко раздражаюсь", "points": 1},
                 {"text": "Иногда я раздражаюсь", "points": 2},
                 {"text": "Обычно я терпелив(а)", "points": 3},
             ],
             "options_zh": [
                {"text": "我对他人明显缺乏耐心", "points": 0}, {"text": "我容易烦躁或不耐烦", "points": 1},
                {"text": "偶尔会这样", "points": 2}, {"text": "我通常比较有耐心", "points": 3}]},
             "options_en": [
                 {"text": "I clearly lack patience with others", "points": 0},
                 {"text": "I get irritated easily", "points": 1},
                 {"text": "I sometimes get irritated", "points": 2},
                 {"text": "I’m usually patient", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (желание общаться).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（沟通意愿）：",
             "text_en": "Choose the option that best matches you (willingness to communicate).",
             "options_ru": [
                 {"text": "Я не хочу общаться с людьми", "points": 0},
                 {"text": "Я заметно сократил(а) общение", "points": 1},
                 {"text": "Иногда избегаю общения", "points": 2},
                 {"text": "Я готов(а) общаться", "points": 3},
             ],
             "options_zh": [
                {"text": "我不愿意与他人沟通或交流", "points": 0}, {"text": "我减少了与他人的交流", "points": 1},
                {"text": "偶尔回避沟通", "points": 2}, {"text": "我愿意主动沟通", "points": 3}]},
             "options_en": [
                 {"text": "I don’t want to communicate with others", "points": 0},
                 {"text": "I’ve reduced communication significantly", "points": 1},
                 {"text": "I sometimes avoid communication", "points": 2},
                 {"text": "I’m willing to communicate", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (негативные эмоции).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（负面情绪）：",
             "text_en": "Choose the option that best matches you (negative emotions).",
             "options_ru": [
                 {"text": "Я испытываю сильные негативные эмоции из‑за работы/людей", "points": 0},
                 {"text": "Негативные эмоции возникают часто", "points": 1},
                 {"text": "Иногда возникают", "points": 2},
                 {"text": "Эмоции в целом стабильны", "points": 3},
             ],
             "options_zh": [
                {"text": "我对工作相关的人产生明显负面情绪", "points": 0}, {"text": "经常会有负面情绪", "points": 1},
                {"text": "偶尔出现", "points": 2}, {"text": "情绪基本稳定", "points": 3}]},
             "options_en": [
                 {"text": "I have strong negative feelings about work/people", "points": 0},
                 {"text": "Negative emotions happen often", "points": 1},
                 {"text": "They happen sometimes", "points": 2},
                 {"text": "My emotions are generally stable", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (социальная усталость).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（社交疲劳）：",
             "text_en": "Choose the option that best matches you (social fatigue).",
             "options_ru": [
                 {"text": "Общение с людьми очень меня выматывает", "points": 0},
                 {"text": "Я часто устаю от общения", "points": 1},
                 {"text": "Иногда устаю", "points": 2},
                 {"text": "Я нормально взаимодействую с людьми", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得与人相处让我非常疲惫", "points": 0}, {"text": "我经常感到社交疲劳", "points": 1},
                {"text": "偶尔会有这种感觉", "points": 2}, {"text": "我可以良好地与他人相处", "points": 3}]},
             "options_en": [
                 {"text": "Being around people exhausts me a lot", "points": 0},
                 {"text": "I often feel socially drained", "points": 1},
                 {"text": "I sometimes feel drained", "points": 2},
                 {"text": "I can interact with others well", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (чувство достижения).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（成就感）：",
             "text_en": "Choose the option that best matches you (sense of achievement).",
             "options_ru": [
                 {"text": "Я не чувствую достижений в работе", "points": 0},
                 {"text": "Чувство достижений низкое", "points": 1},
                 {"text": "Иногда я чувствую достижения", "points": 2},
                 {"text": "Я часто чувствую достижения", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己在工作中毫无成就", "points": 0}, {"text": "我的成就感较低", "points": 1},
                {"text": "我有一定成就感", "points": 2}, {"text": "我有较强的成就感", "points": 3}]},
             "options_en": [
                 {"text": "I feel no sense of achievement at work", "points": 0},
                 {"text": "My sense of achievement is low", "points": 1},
                 {"text": "I sometimes feel a sense of achievement", "points": 2},
                 {"text": "I often feel a strong sense of achievement", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (уверенность).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（自信程度）：",
             "text_en": "Choose the option that best matches you (confidence).",
             "options_ru": [
                 {"text": "Мне кажется, я не справляюсь и некомпетентен(а)", "points": 0},
                 {"text": "У меня часто не хватает уверенности", "points": 1},
                 {"text": "В целом я справляюсь", "points": 2},
                 {"text": "Я уверен(а) в своих способностях", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己能力不足，难以胜任工作", "points": 0}, {"text": "我对自己不太有信心", "points": 1},
                {"text": "我基本可以胜任", "points": 2}, {"text": "我对自己的能力有信心", "points": 3}]},
             "options_en": [
                 {"text": "I feel incompetent and unable to do my work", "points": 0},
                 {"text": "I often lack confidence", "points": 1},
                 {"text": "I can generally manage", "points": 2},
                 {"text": "I’m confident in my abilities", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (ценность работы).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作价值）：",
             "text_en": "Choose the option that best matches you (value of work).",
             "options_ru": [
                 {"text": "Мне кажется, моя работа бессмысленна", "points": 0},
                 {"text": "Я редко вижу ценность в работе", "points": 1},
                 {"text": "Иногда я вижу ценность", "points": 2},
                 {"text": "Я считаю, что моя работа важна", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己的工作没有意义或价值", "points": 0}, {"text": "我觉得价值感较低", "points": 1},
                {"text": "我觉得工作有一定价值", "points": 2}, {"text": "我认为工作具有重要意义", "points": 3}]},
             "options_en": [
                 {"text": "I feel my work has no meaning or value", "points": 0},
                 {"text": "I feel my work has low value", "points": 1},
                 {"text": "I see some value in my work", "points": 2},
                 {"text": "I believe my work is meaningful", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (помощь другим).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（帮助他人）：",
             "text_en": "Choose the option that best matches you (helping others).",
             "options_ru": [
                 {"text": "Мне кажется, я не могу эффективно помогать другим", "points": 0},
                 {"text": "Я помогаю ограниченно", "points": 1},
                 {"text": "Иногда я могу помочь", "points": 2},
                 {"text": "Я могу эффективно помогать", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己无法有效帮助他人", "points": 0}, {"text": "我的帮助能力有限", "points": 1},
                {"text": "我可以提供一定帮助", "points": 2}, {"text": "我能够有效帮助他人", "points": 3}]},
             "options_en": [
                 {"text": "I feel unable to help others effectively", "points": 0},
                 {"text": "My ability to help is limited", "points": 1},
                 {"text": "I can provide some help", "points": 2},
                 {"text": "I can help others effectively", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (удовлетворенность работой).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作满意度）：",
             "text_en": "Choose the option that best matches you (job satisfaction).",
             "options_ru": [
                 {"text": "Я крайне недоволен(а) своей работой", "points": 0},
                 {"text": "Я скорее недоволен(а)", "points": 1},
                 {"text": "Я в целом удовлетворён(а)", "points": 2},
                 {"text": "Я очень доволен(а) своей работой", "points": 3},
             ],
             "options_zh": [
                {"text": "我对自己的工作表现非常不满意", "points": 0}, {"text": "我对表现不太满意", "points": 1},
                {"text": "我基本满意", "points": 2}, {"text": "我对表现很满意", "points": 3}]},
             "options_en": [
                 {"text": "I’m very dissatisfied with my performance", "points": 0},
                 {"text": "I’m somewhat dissatisfied", "points": 1},
                 {"text": "I’m mostly satisfied", "points": 2},
                 {"text": "I’m very satisfied", "points": 3},
             ]},
            {"text_ru": "Выберите утверждение, которое лучше всего описывает ваше состояние (личный рост).",
             "text_zh": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（个人成长）：",
             "text_en": "Choose the option that best matches you (personal growth).",
             "options_ru": [
                 {"text": "Я не вижу никакого роста", "points": 0},
                 {"text": "Мой рост ограничен", "points": 1},
                 {"text": "Есть некоторый рост", "points": 2},
                 {"text": "Я постоянно развиваюсь", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己在职业或学习中没有成长", "points": 0}, {"text": "我的成长较为有限", "points": 1},
                {"text": "我有一定成长", "points": 2}, {"text": "我持续在成长和进步", "points": 3}]},
        ],
    },
    {
        "title_ru": "Оценка уровня тревожности",
        "title_zh": "焦虑状态评估量表",
        "title_en": "Anxiety Level Assessment",
        "description_ru": "Оцените текущий уровень тревожности по ощущениям и симптомам.",
        "description_zh": "评估您当前的焦虑水平",
        "description_en": "Assess your current anxiety level based on feelings and symptoms.",
        "questions": [
            {"text_ru": "Чувство напряжения", "text_zh": "紧张感", "text_en": "Feeling tense",
             "options_ru": [
                 {"text": "Почти постоянно сильное напряжение", "points": 0},
                 {"text": "Часто чувствую напряжение", "points": 1},
                 {"text": "Иногда чувствую напряжение", "points": 2},
                 {"text": "Редко чувствую напряжение", "points": 3},
             ],
             "options_zh": [
                {"text": "我几乎一直处于高度紧张状态", "points": 0}, {"text": "我经常感到紧张", "points": 1},
                {"text": "我偶尔感到紧张", "points": 2}, {"text": "我很少感到紧张", "points": 3}]},
             "options_en": [
                 {"text": "I feel highly tense almost all the time", "points": 0},
                 {"text": "I often feel tense", "points": 1},
                 {"text": "I sometimes feel tense", "points": 2},
                 {"text": "I rarely feel tense", "points": 3},
             ]},
            {"text_ru": "Трудно расслабиться", "text_zh": "无法放松", "text_en": "Unable to relax",
             "options_ru": [
                 {"text": "Совсем не могу расслабиться", "points": 0},
                 {"text": "Мне трудно расслабиться", "points": 1},
                 {"text": "Иногда могу расслабиться", "points": 2},
                 {"text": "Легко расслабляюсь", "points": 3},
             ],
             "options_zh": [
                {"text": "我完全无法放松", "points": 0}, {"text": "我很难放松", "points": 1},
                {"text": "我有时可以放松", "points": 2}, {"text": "我可以轻松放松", "points": 3}]},
             "options_en": [
                 {"text": "I can't relax at all", "points": 0},
                 {"text": "It's hard for me to relax", "points": 1},
                 {"text": "I can relax sometimes", "points": 2},
                 {"text": "I can relax easily", "points": 3},
             ]},
            {"text_ru": "Тревога из-за неизвестности", "text_zh": "对未知的担忧", "text_en": "Worry about the unknown",
             "options_ru": [
                 {"text": "Сильный страх будущего/неизвестности", "points": 0},
                 {"text": "Часто переживаю о будущем", "points": 1},
                 {"text": "Иногда переживаю", "points": 2},
                 {"text": "Редко переживаю", "points": 3},
             ],
             "options_zh": [
                {"text": "我对未来或未知感到强烈恐惧", "points": 0}, {"text": "我经常担心未来", "points": 1},
                {"text": "我有一些担忧", "points": 2}, {"text": "我很少担忧", "points": 3}]},
             "options_en": [
                 {"text": "I feel strong fear about the future/unknown", "points": 0},
                 {"text": "I often worry about the future", "points": 1},
                 {"text": "I have some worries", "points": 2},
                 {"text": "I rarely worry", "points": 3},
             ]},
            {"text_ru": "Учащённое сердцебиение", "text_zh": "心跳加快", "text_en": "Rapid heartbeat",
             "options_ru": [
                 {"text": "Часто сильное учащение", "points": 0},
                 {"text": "Иногда учащается", "points": 1},
                 {"text": "Редко", "points": 2},
                 {"text": "Почти нет", "points": 3},
             ],
             "options_zh": [
                {"text": "我经常感到心跳异常快或强烈", "points": 0}, {"text": "我有时会心跳加快", "points": 1},
                {"text": "偶尔出现", "points": 2}, {"text": "几乎没有", "points": 3}]},
             "options_en": [
                 {"text": "I often feel my heart racing strongly", "points": 0},
                 {"text": "My heartbeat speeds up sometimes", "points": 1},
                 {"text": "It happens occasionally", "points": 2},
                 {"text": "Almost never", "points": 3},
             ]},
            {"text_ru": "Трудности с дыханием", "text_zh": "呼吸困难", "text_en": "Difficulty breathing",
             "options_ru": [
                 {"text": "Часто сложно дышать", "points": 0},
                 {"text": "Иногда дыхание сбивается", "points": 1},
                 {"text": "Редко", "points": 2},
                 {"text": "Нет", "points": 3},
             ],
             "options_zh": [
                {"text": "我经常感到呼吸困难", "points": 0}, {"text": "有时感到呼吸不顺", "points": 1},
                {"text": "偶尔出现", "points": 2}, {"text": "没有这种情况", "points": 3}]},
             "options_en": [
                 {"text": "I often have difficulty breathing", "points": 0},
                 {"text": "My breathing feels off sometimes", "points": 1},
                 {"text": "It happens occasionally", "points": 2},
                 {"text": "Not at all", "points": 3},
             ]},
            {"text_ru": "Потливость", "text_zh": "出汗", "text_en": "Sweating",
             "options_ru": [
                 {"text": "Часто потею без причины", "points": 0},
                 {"text": "Иногда потею необычно сильно", "points": 1},
                 {"text": "Редко", "points": 2},
                 {"text": "Нормально", "points": 3},
             ],
             "options_zh": [
                {"text": "即使不热也经常出汗", "points": 0}, {"text": "有时会异常出汗", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "正常", "points": 3}]},
             "options_en": [
                 {"text": "I often sweat even when it's not hot", "points": 0},
                 {"text": "I sometimes sweat unusually", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Дрожь (руки/тело)", "text_zh": "手抖或身体发抖", "text_en": "Trembling",
             "options_ru": [
                 {"text": "Часто заметная дрожь", "points": 0},
                 {"text": "Иногда дрожу", "points": 1},
                 {"text": "Редко", "points": 2},
                 {"text": "Нет", "points": 3},
             ],
             "options_zh": [
                {"text": "经常明显发抖", "points": 0}, {"text": "有时发抖", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "没有", "points": 3}]},
             "options_en": [
                 {"text": "I often tremble noticeably", "points": 0},
                 {"text": "I sometimes tremble", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "Not at all", "points": 3},
             ]},
            {"text_ru": "Страх потерять контроль", "text_zh": "害怕失控", "text_en": "Fear of losing control",
             "options_ru": [
                 {"text": "Часто кажется, что потеряю контроль", "points": 0},
                 {"text": "Иногда боюсь потерять контроль", "points": 1},
                 {"text": "Редко", "points": 2},
                 {"text": "Обычно контролирую эмоции", "points": 3},
             ],
             "options_zh": [
                {"text": "我经常觉得自己会失去控制", "points": 0}, {"text": "我有时担心失控", "points": 1},
                {"text": "偶尔有这种感觉", "points": 2}, {"text": "我感觉自己可以控制情绪", "points": 3}]},
             "options_en": [
                 {"text": "I often feel like I'm losing control", "points": 0},
                 {"text": "I sometimes worry about losing control", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "I can control my emotions", "points": 3},
             ]},
            {"text_ru": "Катастрофизация", "text_zh": "灾难化思维", "text_en": "Catastrophizing",
             "options_ru": [
                 {"text": "Почти всегда ожидаю худшего", "points": 0},
                 {"text": "Часто думаю о худшем", "points": 1},
                 {"text": "Иногда так бывает", "points": 2},
                 {"text": "Обычно думаю рационально", "points": 3},
             ],
             "options_zh": [
                {"text": "我经常预想最坏结果", "points": 0}, {"text": "我经常往坏处想", "points": 1},
                {"text": "有时会这样", "points": 2}, {"text": "我通常能理性思考", "points": 3}]},
             "options_en": [
                 {"text": "I constantly expect the worst outcome", "points": 0},
                 {"text": "I often think in worst-case scenarios", "points": 1},
                 {"text": "Sometimes", "points": 2},
                 {"text": "I can usually think rationally", "points": 3},
             ]},
            {"text_ru": "Невозможно усидеть на месте", "text_zh": "坐立不安", "text_en": "Restlessness",
             "options_ru": [
                 {"text": "Почти не могу сидеть спокойно", "points": 0},
                 {"text": "Часто чувствую беспокойство", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Обычно спокоен(на)", "points": 3},
             ],
             "options_zh": [
                {"text": "我几乎无法静下来", "points": 0}, {"text": "我经常感到不安", "points": 1},
                {"text": "偶尔不安", "points": 2}, {"text": "我可以保持平静", "points": 3}]},
             "options_en": [
                 {"text": "I can hardly stay still", "points": 0},
                 {"text": "I often feel restless", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "I can stay calm", "points": 3},
             ]},
            {"text_ru": "Легко пугаюсь", "text_zh": "易受惊吓", "text_en": "Easily startled",
             "options_ru": [
                 {"text": "Очень легко пугаюсь", "points": 0},
                 {"text": "Пугаюсь чаще, чем раньше", "points": 1},
                 {"text": "Есть небольшие изменения", "points": 2},
                 {"text": "Обычно", "points": 3},
             ],
             "options_zh": [
                {"text": "我非常容易受到惊吓", "points": 0}, {"text": "我比以前更容易受惊", "points": 1},
                {"text": "有一点变化", "points": 2}, {"text": "正常", "points": 3}]},
             "options_en": [
                 {"text": "I get startled very easily", "points": 0},
                 {"text": "I get startled more than before", "points": 1},
                 {"text": "A slight change", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Трудно концентрироваться", "text_zh": "注意力困难", "text_en": "Difficulty concentrating",
             "options_ru": [
                 {"text": "Почти не могу сосредоточиться", "points": 0},
                 {"text": "Сложно концентрироваться", "points": 1},
                 {"text": "Иногда сложно", "points": 2},
                 {"text": "Нормально", "points": 3},
             ],
             "options_zh": [
                {"text": "我几乎无法集中注意力", "points": 0}, {"text": "很难集中", "points": 1},
                {"text": "偶尔困难", "points": 2}, {"text": "正常", "points": 3}]},
             "options_en": [
                 {"text": "I can barely concentrate", "points": 0},
                 {"text": "It's hard to focus", "points": 1},
                 {"text": "Sometimes it's hard", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Повышенная настороженность", "text_zh": "过度警觉", "text_en": "Hypervigilance",
             "options_ru": [
                 {"text": "Постоянно насторожен(а)", "points": 0},
                 {"text": "Часто напряжён(а)", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Обычно расслаблен(а)", "points": 3},
             ],
             "options_zh": [
                {"text": "我一直处于警觉状态", "points": 0}, {"text": "经常紧绷", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "放松正常", "points": 3}]},
             "options_en": [
                 {"text": "I’m constantly on alert", "points": 0},
                 {"text": "I often feel on edge", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "I feel relaxed normally", "points": 3},
             ]},
            {"text_ru": "Тревога из-за телесных симптомов", "text_zh": "对身体不适的担忧", "text_en": "Worry about physical symptoms",
             "options_ru": [
                 {"text": "Очень переживаю о симптомах", "points": 0},
                 {"text": "Часто переживаю", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Не переживаю", "points": 3},
             ],
             "options_zh": [
                {"text": "我非常担心身体症状", "points": 0}, {"text": "经常担心", "points": 1},
                {"text": "偶尔担心", "points": 2}, {"text": "不担心", "points": 3}]},
             "options_en": [
                 {"text": "I worry a lot about physical symptoms", "points": 0},
                 {"text": "I often worry", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "I don’t worry", "points": 3},
             ]},
            {"text_ru": "Проблемы со сном", "text_zh": "失眠或难以入睡", "text_en": "Sleep problems",
             "options_ru": [
                 {"text": "Сильно влияет на сон", "points": 0},
                 {"text": "Часто трудно уснуть", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Сон нормальный", "points": 3},
             ],
             "options_zh": [
                {"text": "严重影响睡眠", "points": 0}, {"text": "经常难入睡", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "睡眠正常", "points": 3}]},
             "options_en": [
                 {"text": "It severely affects my sleep", "points": 0},
                 {"text": "I often struggle to fall asleep", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "My sleep is normal", "points": 3},
             ]},
            {"text_ru": "Мышечное напряжение", "text_zh": "肌肉紧张", "text_en": "Muscle tension",
             "options_ru": [
                 {"text": "Постоянное напряжение/боль", "points": 0},
                 {"text": "Часто напряжён(а)", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Расслаблен(а)", "points": 3},
             ],
             "options_zh": [
                {"text": "持续紧张或疼痛", "points": 0}, {"text": "经常紧绷", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "放松", "points": 3}]},
             "options_en": [
                 {"text": "Ongoing tension or pain", "points": 0},
                 {"text": "I often feel tense", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "Relaxed", "points": 3},
             ]},
            {"text_ru": "Избегание", "text_zh": "回避行为", "text_en": "Avoidance",
             "options_ru": [
                 {"text": "Избегаю многих ситуаций", "points": 0},
                 {"text": "Часто избегаю", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Почти не избегаю", "points": 3},
             ],
             "options_zh": [
                {"text": "我避免很多活动或场景", "points": 0}, {"text": "我经常回避", "points": 1},
                {"text": "偶尔回避", "points": 2}, {"text": "我不会刻意回避", "points": 3}]},
             "options_en": [
                 {"text": "I avoid many activities/situations", "points": 0},
                 {"text": "I often avoid things", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "I don’t avoid on purpose", "points": 3},
             ]},
            {"text_ru": "Навязчивые мысли", "text_zh": "反复思考问题", "text_en": "Repetitive thoughts",
             "options_ru": [
                 {"text": "Не могу перестать думать об одном и том же", "points": 0},
                 {"text": "Часто прокручиваю мысли", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Могу контролировать мысли", "points": 3},
             ],
             "options_zh": [
                {"text": "我无法停止反复思考", "points": 0}, {"text": "经常反复想", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "我可以控制思考", "points": 3}]},
             "options_en": [
                 {"text": "I can't stop thinking repeatedly", "points": 0},
                 {"text": "I often ruminate", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "I can control my thoughts", "points": 3},
             ]},
            {"text_ru": "Эффективность работы/учёбы", "text_zh": "工作/学习效率", "text_en": "Work/study efficiency",
             "options_ru": [
                 {"text": "Сильно снизилась", "points": 0},
                 {"text": "Заметно снизилась", "points": 1},
                 {"text": "Слегка снизилась", "points": 2},
                 {"text": "Нормальная", "points": 3},
             ],
             "options_zh": [
                {"text": "严重下降", "points": 0}, {"text": "明显下降", "points": 1},
                {"text": "略有下降", "points": 2}, {"text": "正常", "points": 3}]},
             "options_en": [
                 {"text": "It dropped severely", "points": 0},
                 {"text": "It dropped noticeably", "points": 1},
                 {"text": "It dropped slightly", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Тревога в соц. ситуациях", "text_zh": "社交中的焦虑", "text_en": "Social anxiety",
             "options_ru": [
                 {"text": "Я очень боюсь общения", "points": 0},
                 {"text": "Часто тревожусь", "points": 1},
                 {"text": "Немного", "points": 2},
                 {"text": "Не тревожусь", "points": 3},
             ],
             "options_zh": [
                {"text": "我非常害怕社交", "points": 0}, {"text": "我经常焦虑", "points": 1},
                {"text": "有一点", "points": 2}, {"text": "不焦虑", "points": 3}]},
             "options_en": [
                 {"text": "I’m very afraid of social situations", "points": 0},
                 {"text": "I often feel anxious", "points": 1},
                 {"text": "A little", "points": 2},
                 {"text": "Not anxious", "points": 3},
             ]},
            {"text_ru": "Общий уровень тревоги", "text_zh": "整体焦虑水平", "text_en": "Overall anxiety level",
             "options_ru": [
                 {"text": "Сильно мешает жизни", "points": 0},
                 {"text": "Сильно влияет", "points": 1},
                 {"text": "Есть влияние", "points": 2},
                 {"text": "Почти не влияет", "points": 3},
             ],
             "options_zh": [
                {"text": "我的焦虑严重影响生活", "points": 0}, {"text": "我的焦虑影响较大", "points": 1},
                {"text": "有一定影响", "points": 2}, {"text": "基本没有影响", "points": 3}]},
        ],
    },
    {
        "title_ru": "Оценка уровня депрессивного состояния",
        "title_zh": "抑郁状态评估量表",
        "title_en": "Depression Level Assessment",
        "description_ru": "Оцените текущий уровень депрессивных симптомов.",
        "description_zh": "评估您当前的抑郁水平",
        "description_en": "Assess your current depression symptoms level.",
        "questions": [
            {"text_ru": "Эмоциональное состояние", "text_zh": "情绪状态", "text_en": "Emotional state",
             "options_ru": [
                 {"text": "Почти постоянно сильная тоска/безнадёжность", "points": 0},
                 {"text": "Часто грустно в течение долгого времени", "points": 1},
                 {"text": "Иногда грустно", "points": 2},
                 {"text": "Эмоции в целом стабильны", "points": 3},
             ],
             "options_zh": [
                {"text": "我持续感到极度悲伤或绝望，这种情绪几乎无法缓解", "points": 0}, {"text": "我经常感到悲伤，且这种情绪持续时间较长", "points": 1},
                {"text": "我偶尔会感到悲伤或情绪低落", "points": 2}, {"text": "我的情绪基本稳定，很少感到悲伤", "points": 3}]},
             "options_en": [
                 {"text": "I feel extreme sadness/hopelessness almost constantly", "points": 0},
                 {"text": "I often feel sad for long periods", "points": 1},
                 {"text": "I sometimes feel sad", "points": 2},
                 {"text": "My mood is generally stable", "points": 3},
             ]},
            {"text_ru": "Отношение к будущему", "text_zh": "对未来的态度", "text_en": "Attitude toward the future",
             "options_ru": [
                 {"text": "Полная безнадёжность", "points": 0},
                 {"text": "Сильный пессимизм", "points": 1},
                 {"text": "Есть тревога, но остаётся надежда", "points": 2},
                 {"text": "В целом оптимизм", "points": 3},
             ],
             "options_zh": [
                {"text": "我对未来完全感到绝望，看不到任何希望", "points": 0}, {"text": "我对未来感到悲观，认为情况不会变好", "points": 1},
                {"text": "我对未来有一定担忧，但仍保留部分希望", "points": 2}, {"text": "我对未来持积极态度，相信事情会变好", "points": 3}]},
             "options_en": [
                 {"text": "I feel completely hopeless", "points": 0},
                 {"text": "I feel very pessimistic", "points": 1},
                 {"text": "I worry but still have some hope", "points": 2},
                 {"text": "I feel generally optimistic", "points": 3},
             ]},
            {"text_ru": "Ощущение неудачи", "text_zh": "失败感", "text_en": "Sense of failure",
             "options_ru": [
                 {"text": "Моя жизнь кажется провалом", "points": 0},
                 {"text": "Я чувствую себя более неуспешным(ой), чем другие", "points": 1},
                 {"text": "Бывают неудачи, но это нормально", "points": 2},
                 {"text": "В целом я ценен(на) и успешен(на)", "points": 3},
             ],
             "options_zh": [
                {"text": "我认为自己的人生是失败的，几乎没有成功之处", "points": 0}, {"text": "我觉得自己比大多数人更失败", "points": 1},
                {"text": "我认为自己有过一些失败，但也有正常表现", "points": 2}, {"text": "我认为自己整体是成功的或有价值的", "points": 3}]},
             "options_en": [
                 {"text": "I feel my life is a failure", "points": 0},
                 {"text": "I feel more like a failure than most people", "points": 1},
                 {"text": "I've had failures but also normal performance", "points": 2},
                 {"text": "I feel generally successful/valuable", "points": 3},
             ]},
            {"text_ru": "Удовлетворённость", "text_zh": "满足感", "text_en": "Satisfaction",
             "options_ru": [
                 {"text": "Ничто не приносит радости", "points": 0},
                 {"text": "Редко получаю удовольствие", "points": 1},
                 {"text": "Удовольствия меньше, чем раньше", "points": 2},
                 {"text": "В целом могу радоваться", "points": 3},
             ],
             "options_zh": [
                {"text": "我对生活中的任何事情都无法感到满足或快乐", "points": 0}, {"text": "我很少从生活中获得满足感", "points": 1},
                {"text": "我的满足感比以前有所下降", "points": 2}, {"text": "我仍然能够从生活中获得满足和快乐", "points": 3}]},
             "options_en": [
                 {"text": "Nothing brings me satisfaction or joy", "points": 0},
                 {"text": "I rarely feel satisfied", "points": 1},
                 {"text": "I feel less satisfaction than before", "points": 2},
                 {"text": "I can still feel satisfied/joyful", "points": 3},
             ]},
            {"text_ru": "Чувство вины", "text_zh": "内疚感", "text_en": "Guilt",
             "options_ru": [
                 {"text": "Сильная постоянная вина", "points": 0},
                 {"text": "Часто чувствую вину", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Редко/нет", "points": 3},
             ],
             "options_zh": [
                {"text": "我持续感到强烈的内疚，甚至为很多事情责怪自己", "points": 0}, {"text": "我经常感到内疚", "points": 1},
                {"text": "我偶尔会感到内疚", "points": 2}, {"text": "我很少或几乎不感到内疚", "points": 3}]},
             "options_en": [
                 {"text": "I feel intense guilt constantly", "points": 0},
                 {"text": "I often feel guilty", "points": 1},
                 {"text": "Sometimes", "points": 2},
                 {"text": "Rarely / not at all", "points": 3},
             ]},
            {"text_ru": "Ощущение наказания", "text_zh": "惩罚感", "text_en": "Feeling punished",
             "options_ru": [
                 {"text": "Кажется, что я заслуживаю наказания", "points": 0},
                 {"text": "Есть ощущение, что меня “накажут”", "points": 1},
                 {"text": "Небольшая тревога", "points": 2},
                 {"text": "Нет", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己正在受到惩罚或理应受到惩罚", "points": 0}, {"text": "我感觉可能会受到惩罚", "points": 1},
                {"text": "我对被惩罚有轻微担心", "points": 2}, {"text": "我没有这种感觉", "points": 3}]},
             "options_en": [
                 {"text": "I feel I'm being punished / deserve punishment", "points": 0},
                 {"text": "I feel I might be punished", "points": 1},
                 {"text": "A slight worry", "points": 2},
                 {"text": "Not at all", "points": 3},
             ]},
            {"text_ru": "Самооценка", "text_zh": "自我评价", "text_en": "Self-esteem",
             "options_ru": [
                 {"text": "Я крайне недоволен(а) собой", "points": 0},
                 {"text": "Я не очень доволен(а) собой", "points": 1},
                 {"text": "В целом принимаю себя", "points": 2},
                 {"text": "Отношусь к себе позитивно", "points": 3},
             ],
             "options_zh": [
                {"text": "我对自己极度不满，甚至厌恶自己", "points": 0}, {"text": "我对自己不太满意", "points": 1},
                {"text": "我基本可以接受自己", "points": 2}, {"text": "我对自己持积极评价", "points": 3}]},
             "options_en": [
                 {"text": "I strongly dislike myself", "points": 0},
                 {"text": "I'm not very satisfied with myself", "points": 1},
                 {"text": "I can mostly accept myself", "points": 2},
                 {"text": "I have a positive view of myself", "points": 3},
             ]},
            {"text_ru": "Самокритика", "text_zh": "自我批评", "text_en": "Self-criticism",
             "options_ru": [
                 {"text": "Постоянно жестко критикую себя", "points": 0},
                 {"text": "Часто виню себя", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Редко", "points": 3},
             ],
             "options_zh": [
                {"text": "我经常严厉批评自己，甚至认为自己一无是处", "points": 0}, {"text": "我经常责备自己的错误", "points": 1},
                {"text": "我有时会责备自己", "points": 2}, {"text": "我很少责备自己", "points": 3}]},
             "options_en": [
                 {"text": "I constantly criticize myself harshly", "points": 0},
                 {"text": "I often blame myself", "points": 1},
                 {"text": "Sometimes", "points": 2},
                 {"text": "Rarely", "points": 3},
             ]},
            {"text_ru": "Мысли о самоповреждении/суициде", "text_zh": "自杀想法", "text_en": "Suicidal thoughts",
             "options_ru": [
                 {"text": "Частые мысли, включая планы", "points": 0},
                 {"text": "Бывают мысли, но без действий", "points": 1},
                 {"text": "Редко и быстро проходят", "points": 2},
                 {"text": "Нет", "points": 3},
             ],
             "options_zh": [
                {"text": "我经常有自杀的想法，甚至考虑实施", "points": 0}, {"text": "我有过自杀想法，但不会付诸行动", "points": 1},
                {"text": "我偶尔会想到，但很快消失", "points": 2}, {"text": "我完全没有这种想法", "points": 3}]},
             "options_en": [
                 {"text": "I often have suicidal thoughts and consider acting", "points": 0},
                 {"text": "I have thoughts but won’t act", "points": 1},
                 {"text": "Occasionally, then they pass", "points": 2},
                 {"text": "Not at all", "points": 3},
             ]},
            {"text_ru": "Плаксивость", "text_zh": "哭泣", "text_en": "Crying",
             "options_ru": [
                 {"text": "Почти каждый день хочется плакать", "points": 0},
                 {"text": "Плачу чаще, чем раньше", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Редко/нет", "points": 3},
             ],
             "options_zh": [
                {"text": "我几乎每天都想哭或经常哭泣", "points": 0}, {"text": "我比以前更容易哭", "points": 1},
                {"text": "我偶尔会哭", "points": 2}, {"text": "我基本不哭", "points": 3}]},
             "options_en": [
                 {"text": "I feel like crying almost every day", "points": 0},
                 {"text": "I cry more than before", "points": 1},
                 {"text": "Sometimes", "points": 2},
                 {"text": "Rarely / not at all", "points": 3},
             ]},
            {"text_ru": "Раздражительность", "text_zh": "易怒", "text_en": "Irritability",
             "options_ru": [
                 {"text": "Я гораздо более раздражителен(на)", "points": 0},
                 {"text": "Часто раздражаюсь", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Обычно спокоен(на)", "points": 3},
             ],
             "options_zh": [
                {"text": "我比以前明显更容易生气或烦躁", "points": 0}, {"text": "我经常感到烦躁", "points": 1},
                {"text": "我偶尔会烦躁", "points": 2}, {"text": "我情绪平稳，不易生气", "points": 3}]},
             "options_en": [
                 {"text": "I'm much more irritable than before", "points": 0},
                 {"text": "I often feel irritable", "points": 1},
                 {"text": "Sometimes", "points": 2},
                 {"text": "I’m generally calm", "points": 3},
             ]},
            {"text_ru": "Интерес к общению", "text_zh": "社交兴趣", "text_en": "Social interest",
             "options_ru": [
                 {"text": "Полностью теряю интерес к людям", "points": 0},
                 {"text": "Меньше участвую в общении", "points": 1},
                 {"text": "Интерес немного снизился", "points": 2},
                 {"text": "Интерес нормальный", "points": 3},
             ],
             "options_zh": [
                {"text": "我对他人完全失去兴趣，避免社交", "points": 0}, {"text": "我比以前更少参与社交活动", "points": 1},
                {"text": "我的社交兴趣略有下降", "points": 2}, {"text": "我保持正常的社交兴趣", "points": 3}]},
             "options_en": [
                 {"text": "I have no interest in others and avoid socializing", "points": 0},
                 {"text": "I socialize less than before", "points": 1},
                 {"text": "My interest decreased slightly", "points": 2},
                 {"text": "My interest is normal", "points": 3},
             ]},
            {"text_ru": "Принятие решений", "text_zh": "决策能力", "text_en": "Decision-making",
             "options_ru": [
                 {"text": "Почти не могу принимать решения", "points": 0},
                 {"text": "Очень трудно", "points": 1},
                 {"text": "Чуть труднее, чем раньше", "points": 2},
                 {"text": "Нормально", "points": 3},
             ],
             "options_zh": [
                {"text": "我几乎无法做出任何决定", "points": 0}, {"text": "我做决定时非常困难", "points": 1},
                {"text": "我做决定比以前稍慢", "points": 2}, {"text": "我做决定能力正常", "points": 3}]},
             "options_en": [
                 {"text": "I can hardly make any decisions", "points": 0},
                 {"text": "Making decisions is very difficult", "points": 1},
                 {"text": "It's a bit harder than before", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Чувство собственной ценности", "text_zh": "自我价值感", "text_en": "Self-worth",
             "options_ru": [
                 {"text": "Я чувствую себя никчёмным(ой)", "points": 0},
                 {"text": "Ценность кажется низкой", "points": 1},
                 {"text": "Иногда признаю свою ценность", "points": 2},
                 {"text": "Я считаю себя ценным человеком", "points": 3},
             ],
             "options_zh": [
                {"text": "我觉得自己毫无价值", "points": 0}, {"text": "我觉得自己价值较低", "points": 1},
                {"text": "我对自己有一定认可", "points": 2}, {"text": "我认为自己是有价值的人", "points": 3}]},
             "options_en": [
                 {"text": "I feel worthless", "points": 0},
                 {"text": "I feel low self-worth", "points": 1},
                 {"text": "I sometimes recognize my value", "points": 2},
                 {"text": "I believe I’m a valuable person", "points": 3},
             ]},
            {"text_ru": "Уровень энергии", "text_zh": "精力水平", "text_en": "Energy level",
             "options_ru": [
                 {"text": "Нет сил ни на что", "points": 0},
                 {"text": "Быстро устаю", "points": 1},
                 {"text": "Иногда устаю", "points": 2},
                 {"text": "Энергия нормальная", "points": 3},
             ],
             "options_zh": [
                {"text": "我几乎没有精力做任何事情", "points": 0}, {"text": "我很容易疲劳", "points": 1},
                {"text": "我有时感到疲劳", "points": 2}, {"text": "我的精力基本正常", "points": 3}]},
             "options_en": [
                 {"text": "I have almost no energy for anything", "points": 0},
                 {"text": "I get tired easily", "points": 1},
                 {"text": "I sometimes feel tired", "points": 2},
                 {"text": "My energy is generally normal", "points": 3},
             ]},
            {"text_ru": "Сон", "text_zh": "睡眠状况", "text_en": "Sleep",
             "options_ru": [
                 {"text": "Сильно нарушен", "points": 0},
                 {"text": "Качество плохое", "points": 1},
                 {"text": "Есть небольшие проблемы", "points": 2},
                 {"text": "Нормально", "points": 3},
             ],
             "options_zh": [
                {"text": "我的睡眠严重紊乱（失眠或过度睡眠）", "points": 0}, {"text": "我的睡眠质量较差", "points": 1},
                {"text": "睡眠略有问题", "points": 2}, {"text": "睡眠正常", "points": 3}]},
             "options_en": [
                 {"text": "My sleep is severely disrupted", "points": 0},
                 {"text": "My sleep quality is poor", "points": 1},
                 {"text": "Slight problems", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Изменения аппетита", "text_zh": "食欲变化", "text_en": "Appetite changes",
             "options_ru": [
                 {"text": "Сильные изменения", "points": 0},
                 {"text": "Аппетит плохой", "points": 1},
                 {"text": "Небольшие изменения", "points": 2},
                 {"text": "Нормально", "points": 3},
             ],
             "options_zh": [
                {"text": "我的食欲严重异常（明显减少或增加）", "points": 0}, {"text": "我的食欲较差", "points": 1},
                {"text": "食欲略有变化", "points": 2}, {"text": "食欲正常", "points": 3}]},
             "options_en": [
                 {"text": "My appetite changed severely", "points": 0},
                 {"text": "My appetite is poor", "points": 1},
                 {"text": "Slight changes", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Забота о здоровье", "text_zh": "健康关注", "text_en": "Health worries",
             "options_ru": [
                 {"text": "Сильно беспокоит и мешает жить", "points": 0},
                 {"text": "Часто беспокоит", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Редко/нет", "points": 3},
             ],
             "options_zh": [
                {"text": "我过度担心身体问题，影响生活", "points": 0}, {"text": "我经常担心健康", "points": 1},
                {"text": "我偶尔担心", "points": 2}, {"text": "我很少担心", "points": 3}]},
             "options_en": [
                 {"text": "I worry excessively and it affects my life", "points": 0},
                 {"text": "I often worry about health", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "Rarely / not at all", "points": 3},
             ]},
            {"text_ru": "Интерес к сексу", "text_zh": "性兴趣", "text_en": "Sexual interest",
             "options_ru": [
                 {"text": "Полностью пропал", "points": 0},
                 {"text": "Заметно снизился", "points": 1},
                 {"text": "Слегка снизился", "points": 2},
                 {"text": "Нормальный", "points": 3},
             ],
             "options_zh": [
                {"text": "我完全失去性兴趣", "points": 0}, {"text": "性兴趣明显下降", "points": 1},
                {"text": "略有下降", "points": 2}, {"text": "正常", "points": 3}]},
             "options_en": [
                 {"text": "I completely lost interest", "points": 0},
                 {"text": "It decreased significantly", "points": 1},
                 {"text": "It decreased slightly", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Внимание", "text_zh": "注意力", "text_en": "Attention",
             "options_ru": [
                 {"text": "Совсем не могу сосредоточиться", "points": 0},
                 {"text": "Трудно", "points": 1},
                 {"text": "Иногда", "points": 2},
                 {"text": "Нормально", "points": 3},
             ],
             "options_zh": [
                {"text": "我完全无法集中注意力", "points": 0}, {"text": "我很难集中注意力", "points": 1},
                {"text": "偶尔难以集中", "points": 2}, {"text": "注意力正常", "points": 3}]},
             "options_en": [
                 {"text": "I can't focus at all", "points": 0},
                 {"text": "It's hard to focus", "points": 1},
                 {"text": "Occasionally", "points": 2},
                 {"text": "Normal", "points": 3},
             ]},
            {"text_ru": "Способность действовать", "text_zh": "行动能力", "text_en": "Ability to act",
             "options_ru": [
                 {"text": "Не могу начать или закончить дела", "points": 0},
                 {"text": "Очень трудно", "points": 1},
                 {"text": "Есть трудности", "points": 2},
                 {"text": "Действую нормально", "points": 3},
             ],
             "options_zh": [
                {"text": "我几乎无法开始或完成任何事情", "points": 0}, {"text": "我做事非常困难", "points": 1},
                {"text": "做事有一定困难", "points": 2}, {"text": "我可以正常行动", "points": 3}]},
        ],
    },
]
"""

# Answer tendency per worker: 0=worst, 3=best
WORKER_PROFILES = [
    {"min": 2, "max": 3},  # Ivan - healthy
    {"min": 1, "max": 2},  # Maria - moderate
    {"min": 0, "max": 1},  # Alexey - struggling
    {"min": 1, "max": 3},  # Li Wei - mixed
]

JOURNAL_NOTES_I18N = [
    (4, {"ru": "Хороший день, чувствую себя бодро.", "en": "Good day — I feel energized.", "zh": "今天状态不错，感觉精力充沛。"}),
    (3, {"ru": "Обычный день, немного устал(а).", "en": "An ordinary day — a bit tired.", "zh": "普通的一天，有点累。"}),
    (2, {"ru": "Тяжёлый день, много стресса.", "en": "A hard day — lots of stress.", "zh": "很难的一天，压力很大。"}),
    (5, {"ru": "Отличное настроение!", "en": "Great mood!", "zh": "心情很好！"}),
    (1, {"ru": "Очень плохо себя чувствую.", "en": "I feel really bad.", "zh": "我感觉很糟糕。"}),
    (3, None),
    (4, {"ru": "Продуктивный день.", "en": "A productive day.", "zh": "今天很有成效。"}),
]

JOURNAL_PHRASES_I18N: dict[str, list[str]] = {
    "ru": [
        "Сегодня получилось сосредоточиться на задачах.",
        "Было сложно из-за дедлайнов, но в целом справился(ась).",
        "Чувствую усталость, хотелось бы больше отдыха.",
        "Поймал(а) себя на тревожных мыслях, сделал(а) паузу и стало легче.",
        "Настроение нестабильное, но есть ощущение прогресса.",
        "Немного раздражительность, возможно из-за сна.",
        "Сон был лучше, энергии больше.",
        "Было трудно общаться, хотелось побыть одному/одной.",
    ],
    "en": [
        "I managed to focus on my tasks today.",
        "Deadlines were stressful, but I got through it.",
        "I feel tired and could really use more rest.",
        "I noticed anxious thoughts, took a short break, and it helped.",
        "My mood was unstable, but I still feel some progress.",
        "A bit irritable — maybe because of sleep.",
        "Sleep was better, and I had more energy.",
        "Social interaction felt difficult; I wanted to be alone for a while.",
    ],
    "zh": [
        "今天能更专注地处理任务。",
        "截止时间带来压力，但总体上还是应付过来了。",
        "感觉很疲惫，需要更多休息。",
        "注意到自己在焦虑反刍，停下来休息一下后好一些。",
        "情绪有些波动，但还是感觉在进步。",
        "有点烦躁，可能和睡眠有关。",
        "睡得更好了，精力也多一些。",
        "社交有点吃力，想一个人待一会儿。",
    ],
}


def _rand_dt_between(start: datetime, end: datetime) -> datetime:
    if end <= start:
        return start
    span = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, span))


def _parse_ru_date(s: str) -> date | None:
    s2 = (s or "").strip()
    if not s2:
        return None
    # Examples: "2 февраля 2026", "23 февраля 2026", "6 апреля 2026"
    m = re.match(r"^(\d{1,2})\s+([а-яА-ЯёЁ]+)\s+(\d{4})\s*$", s2)
    if not m:
        return None
    day = int(m.group(1))
    month_name = m.group(2).casefold()
    year = int(m.group(3))
    months = {
        "января": 1,
        "февраля": 2,
        "марта": 3,
        "апреля": 4,
        "мая": 5,
        "июня": 6,
        "июля": 7,
        "августа": 8,
        "сентября": 9,
        "октября": 10,
        "ноября": 11,
        "декабря": 12,
    }
    month = months.get(month_name)
    if not month:
        return None
    try:
        return date(year, month, day)
    except Exception:
        return None


def _load_ivan_journals() -> list[dict]:
    """
    Load Ivan's journal entries from backend/ivan_info_{rus,eng,zh}.txt.
    Returns list of:
      {"date": date, "emoji": str|None, "ru": str, "en": str, "zh": str}
    """

    def read_text(rel_path: str) -> str | None:
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel_path))
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return f.read()

    ru_text = read_text("ivan_info_rus.txt")
    en_text = read_text("ivan_info_eng.txt")
    zh_text = read_text("ivan_info_zh.txt")
    if not (ru_text and en_text and zh_text):
        return []

    def split_blocks(txt: str) -> list[str]:
        parts = re.split(r"\n\s*⸻\s*\n", txt.strip(), flags=re.MULTILINE)
        return [p.strip() for p in parts if p and p.strip()]

    ru_blocks = split_blocks(ru_text)
    en_blocks = split_blocks(en_text)
    zh_blocks = split_blocks(zh_text)

    out: list[dict] = []
    n = min(len(ru_blocks), len(en_blocks), len(zh_blocks))
    for i in range(n):
        rb = ru_blocks[i]
        eb = en_blocks[i]
        zb = zh_blocks[i]

        # date line: first line that matches ru date format
        rb_lines = [ln.strip() for ln in rb.splitlines() if ln.strip()]
        eb_lines = [ln.strip() for ln in eb.splitlines() if ln.strip()]
        zb_lines = [ln.strip() for ln in zb.splitlines() if ln.strip()]

        d = None
        for ln in rb_lines[:5]:
            d = _parse_ru_date(ln)
            if d:
                break
        if not d:
            continue

        # emoji from "Настроение: 😣 ..."
        emoji = None
        for ln in rb_lines[:6]:
            m = re.search(r"Настроение\s*[:：]\s*([^\s]+)", ln, flags=re.IGNORECASE)
            if m:
                emoji = m.group(1).strip()
                break

        def extract_body(lines: list[str]) -> str:
            # drop "Иван"/"ivan" header if present, drop date line, drop mood line
            body = []
            for ln in lines:
                if _parse_ru_date(ln):
                    continue
                if re.search(r"^\s*(иван|ivan)\s*$", ln, flags=re.IGNORECASE):
                    continue
                if re.search(r"Настроение\s*[:：]", ln, flags=re.IGNORECASE):
                    continue
                body.append(ln)
            return "\n".join(body).strip()

        ru_body = extract_body(rb_lines)
        en_body = extract_body(eb_lines)
        zh_body = extract_body(zb_lines)
        if not ru_body:
            continue

        out.append({"date": d, "emoji": emoji, "ru": ru_body, "en": en_body, "zh": zh_body})

    return out


def _make_note_i18n(base_map: dict[str, str] | None) -> dict[str, str] | None:
    # Keep some empty notes
    if base_map is None:
        return None

    extra_count = random.choices([0, 1, 2, 3], weights=[35, 35, 20, 10])[0]
    out: dict[str, str] = {}
    for lang in ("ru", "en", "zh"):
        parts = [base_map.get(lang, "").strip()]
        parts = [p for p in parts if p]
        for _ in range(extra_count):
            parts.append(random.choice(JOURNAL_PHRASES_I18N[lang]))
        out[lang] = " ".join(parts).strip()
    return out


def seed_database(db: Session):
    """Populate DB with test data if no users exist."""
    existing_user = db.query(models.User).first()
    if existing_user:
        # Keep users, but fix canon language / reload content if needed.
        therapist = db.query(models.User).filter(models.User.role == models.UserRole.therapist).first()
        therapist_id = therapist.id if therapist else existing_user.id

        if _needs_test_reseed(db):
            _reseed_tests_from_txt(db, therapist_id=therapist_id)

        if _needs_materials_reseed(db):
            _reseed_materials_from_txt(db, author_id=therapist_id)

        return

    logger.info("Database is empty, seeding test data...")

    # Create users
    therapist = models.User(
        full_name=THERAPIST["full_name"], mail=THERAPIST["mail"],
        hashed_password=auth.get_password_hash(THERAPIST["password"]),
        role=models.UserRole.therapist
    )
    db.add(therapist)
    db.flush()

    workers = []
    for w in WORKERS:
        user = models.User(
            full_name=w["full_name"], mail=w["mail"],
            hashed_password=auth.get_password_hash(w["password"]),
            role=models.UserRole.worker
        )
        db.add(user)
        workers.append(user)
    db.flush()

    # Create tests and questions
    all_tests = []
    for test_data in (_load_tests_from_txt() or []):
        # Canonical language in DB: RU. Translations for ZH/EN go into *_translations tables.
        has_ru = bool((test_data.get("title_ru") or "").strip() or (test_data.get("description_ru") or "").strip())
        canonical_lang = "ru" if has_ru else ("en" if (test_data.get("title_en") or "").strip() else "zh")
        test = models.Test(
            title=test_data.get("title_ru") or test_data.get("title_zh") or test_data.get("title_en"),
            description=test_data.get("description_ru") or test_data.get("description_zh") or test_data.get("description_en"),
            therapist_id=therapist.id,
            source_lang=canonical_lang,
        )
        db.add(test)
        db.flush()
        all_tests.append(test)

        # Seed test translations
        for lang, title_key, desc_key in (
            ("zh", "title_zh", "description_zh"),
            ("en", "title_en", "description_en"),
        ):
            title_val = test_data.get(title_key)
            if title_val:
                db.add(models.TestTranslation(
                    test_id=test.id,
                    lang=lang,
                    translated_title=title_val,
                    translated_description=test_data.get(desc_key),
                ))

        for q_data in test_data["questions"]:
            # Canonical question text/options: RU (fallback to ZH/EN if RU missing)
            base_text = q_data.get("text_ru") or q_data.get("text_zh") or q_data.get("text_en")
            base_options = q_data.get("options_ru") or q_data.get("options_zh") or q_data.get("options_en")
            q_has_ru = bool((q_data.get("text_ru") or "").strip())
            q_canonical_lang = "ru" if q_has_ru else ("en" if (q_data.get("text_en") or "").strip() else "zh")
            question = models.Question(text=base_text, options=base_options, test_id=test.id, source_lang=q_canonical_lang)
            db.add(question)
            db.flush()

            # Seed question translations for ZH/EN
            for lang, text_key, options_key in (
                ("zh", "text_zh", "options_zh"),
                ("en", "text_en", "options_en"),
            ):
                t_text = q_data.get(text_key)
                t_opts = q_data.get(options_key)
                if t_text and t_opts:
                    db.add(models.QuestionTranslation(
                        question_id=question.id,
                        lang=lang,
                        translated_text=t_text,
                        translated_options=t_opts,
                    ))
        db.flush()

    # Create materials + translations
    for mat_data in (_load_materials_from_txt() or []):
        base_title = mat_data.get("title_ru") or mat_data.get("title_zh") or mat_data.get("title_en")
        base_content = mat_data.get("content_ru") or mat_data.get("content_zh") or mat_data.get("content_en")
        emoji = (mat_data.get("emoji") or "").strip() or None
        if not base_title or not base_content:
            continue

        has_ru = bool((mat_data.get("title_ru") or "").strip() or (mat_data.get("content_ru") or "").strip())
        canonical_lang = "ru" if has_ru else ("en" if (mat_data.get("title_en") or "").strip() else "zh")
        mat = models.Material(
            title=base_title,
            content=base_content,
            emoji=emoji,
            author_id=therapist.id,
            source_lang=canonical_lang,
        )
        db.add(mat)
        db.flush()

        for lang, title_key, content_key in (
            ("zh", "title_zh", "content_zh"),
            ("en", "title_en", "content_en"),
        ):
            t_title = mat_data.get(title_key)
            t_content = mat_data.get(content_key)
            if t_title and t_content:
                db.add(
                    models.MaterialTranslation(
                        material_id=mat.id,
                        lang=lang,
                        translated_title=t_title,
                        translated_content=t_content,
                    )
                )

    # Workers take tests
    # Wider range of dates: Dec -> Apr (inclusive)
    start_dt = datetime(2025, 12, 1, 9, 0, 0)
    end_dt = datetime(2026, 4, 9, 21, 0, 0)

    for i, worker in enumerate(workers):
        profile = WORKER_PROFILES[i % len(WORKER_PROFILES)]
        # Each worker takes each test multiple times across the date range
        for test in all_tests:
            attempts = random.randint(4, 10)
            for _ in range(attempts):
                total_score = 0
                for question in test.questions:
                    idx = random.randint(profile["min"], min(profile["max"], len(question.options) - 1))
                    total_score += question.options[idx]["points"]

                created_at = _rand_dt_between(start_dt, end_dt)
                result = models.TestResult(
                    total_score=total_score,
                    user_id=worker.id,
                    test_id=test.id,
                    created_at=created_at,
                )
                db.add(result)

        # Journal entries
        is_ivan = (worker.full_name or "").strip().casefold().startswith("иван ")
        if is_ivan:
            ivan_entries = _load_ivan_journals()
            for je in ivan_entries:
                # keep exact dates from the file, add random daytime time
                hh = random.randint(9, 21)
                mm = random.choice([0, 10, 20, 30, 40, 50])
                created_at = datetime(je["date"].year, je["date"].month, je["date"].day, hh, mm, 0)

                ru_text = (je.get("ru") or "").strip()
                if je.get("emoji"):
                    ru_text = f"{je['emoji']} {ru_text}".strip()

                entry = models.Journal(
                    wellbeing_score=random.randint(2, 4),
                    note_text=ru_text,
                    source_lang="ru",
                    user_id=worker.id,
                    created_at=created_at,
                )
                db.add(entry)
                db.flush()

                en_text = (je.get("en") or "").strip()
                zh_text = (je.get("zh") or "").strip()
                if en_text:
                    db.add(models.JournalTranslation(journal_id=entry.id, lang="en", translated_note_text=en_text))
                if zh_text:
                    db.add(models.JournalTranslation(journal_id=entry.id, lang="zh", translated_note_text=zh_text))

            # plus some extra random short/long entries to mix it up
            extra_cnt = random.randint(10, 20)
        else:
            extra_cnt = random.randint(25, 55)

        for _ in range(extra_cnt):
            score, note_map = random.choice(JOURNAL_NOTES_I18N)
            note_i18n = _make_note_i18n(note_map)
            created_at = _rand_dt_between(start_dt, end_dt)
            entry = models.Journal(
                wellbeing_score=score,
                note_text=(note_i18n.get("ru") if note_i18n else None),
                source_lang="ru",
                user_id=worker.id,
                created_at=created_at,
            )
            db.add(entry)
            db.flush()

            if note_i18n:
                en_text = note_i18n.get("en")
                zh_text = note_i18n.get("zh")
                if en_text:
                    db.add(models.JournalTranslation(journal_id=entry.id, lang="en", translated_note_text=en_text))
                if zh_text:
                    db.add(models.JournalTranslation(journal_id=entry.id, lang="zh", translated_note_text=zh_text))

    db.commit()
    logger.info("Seed data created successfully!")
    logger.info("Therapist: %s / %s", THERAPIST["mail"], THERAPIST["password"])
    logger.info("Workers (all %s): %s", WORKERS[0]["password"], ", ".join([w["mail"] for w in WORKERS[:5]]))
