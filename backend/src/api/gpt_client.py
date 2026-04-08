from dotenv import load_dotenv
import logging
import os
from sqlalchemy.orm import Session

import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models

load_dotenv()

from openai import OpenAI

client = OpenAI()
logger = logging.getLogger(__name__)

def _detect_lang(text: str) -> str:
    """Very small heuristic language detection (ru/zh/en) without extra deps."""
    if not text:
        return "en"
    sample = text.strip()
    if not sample:
        return "en"

    # Chinese Han characters
    for ch in sample:
        if "\u4e00" <= ch <= "\u9fff":
            return "zh"

    # Count Cyrillic vs Latin letters
    cyr = 0
    lat = 0
    for ch in sample:
        o = ord(ch)
        if (0x0400 <= o <= 0x04FF) or (0x0500 <= o <= 0x052F):
            cyr += 1
        elif (0x0041 <= o <= 0x005A) or (0x0061 <= o <= 0x007A):
            lat += 1

    if cyr > lat and cyr >= 2:
        return "ru"
    return "en"


def _lang_instruction(lang: str) -> str:
    if lang == "ru":
        return "Отвечай на русском языке."
    if lang == "zh":
        return "请用中文回答。"
    return "Answer in English."


def _normalize_chat_history(chat_history: list | None) -> list[dict]:
    """Convert frontend history ({role,user/ai, text}) to OpenAI messages ({role, content})."""
    if not chat_history:
        return []

    normalized: list[dict] = []
    for msg in chat_history[-20:]:
        role_raw = (msg.get("role") or "").strip().lower()
        text = msg.get("text") or ""

        if role_raw in ("user",):
            role = "user"
        elif role_raw in ("assistant", "ai"):
            role = "assistant"
        elif role_raw in ("system",):
            role = "system"
        else:
            # Unknown role; skip to avoid confusing the model
            continue

        normalized.append({"role": role, "content": text})

    return normalized


def generate_user_summary(user_id: int, db: Session) -> dict:
    try:
        journals = (
            db.query(models.Journal)
            .filter(models.Journal.user_id == user_id)
            .order_by(models.Journal.created_at.desc())
            .limit(10)
            .all()
        )

        tests = (
            db.query(models.TestResult)
            .filter(models.TestResult.user_id == user_id)
            .order_by(models.TestResult.created_at.desc())
            .limit(5)
            .all()
        )

        if not journals and not tests:
            logger.info(f"No data available for user {user_id}, skipping summary generation")
            return {"success": False, "error": "No data available"}

        journal_text = "\n".join(
            [f"- {j.created_at.date()}: {j.note_text} (score: {j.wellbeing_score})"
             for j in journals if j.note_text]
        )

        test_text = "\n".join(
            [f"- {t.created_at.date()}: score {t.total_score}"
             for t in tests]
        )

        prompt = f"""
        Ты психологический ассистент.
        Сделай краткую выжимку состояния пользователя.

        Тесты:
        {test_text if test_text else "Нет данных"}

        Заметки:
        {journal_text if journal_text else "Нет данных"}

        Сформулируй:
        - общее состояние
        - тенденции
        - краткий совет
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты психологический ассистент, который анализирует данные пользователя."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        result = response.choices[0].message.content

        if not result or len(result.strip()) < 10:
            logger.error(f"GPT returned empty or too short response for user {user_id}")
            return {"success": False, "error": "Invalid GPT response"}

        if len(result) > 2000:
            result = result[:2000]

        summary = models.AISummary(user_id=user_id, summary_text=result)
        db.add(summary)
        db.commit()

        logger.info(f"Successfully generated summary for user {user_id}")
        return {"success": True, "error": None}

    except Exception as e:
        logger.error(f"AI summary error for user {user_id}: {e}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}


def _build_user_context(user_id: int, db: Session) -> str:
    """Build full context about the user from all available data."""
    parts = []

    # User info
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        parts.append(f"Имя работника: {user.full_name}")

    # Latest AI summary
    last_summary = (
        db.query(models.AISummary)
        .filter(models.AISummary.user_id == user_id)
        .order_by(models.AISummary.created_at.desc())
        .first()
    )
    if last_summary:
        parts.append(f"Последняя аналитика:\n{last_summary.summary_text}")

    # Recent journals
    journals = (
        db.query(models.Journal)
        .filter(models.Journal.user_id == user_id)
        .order_by(models.Journal.created_at.desc())
        .limit(5)
        .all()
    )
    if journals:
        j_text = "\n".join([
            f"  - {j.created_at.strftime('%d.%m.%Y')}: настроение {j.wellbeing_score}/5"
            + (f", запись: \"{j.note_text[:100]}\"" if j.note_text else "")
            for j in journals
        ])
        parts.append(f"Последние записи журнала:\n{j_text}")

    # Recent test results
    tests = (
        db.query(models.TestResult)
        .filter(models.TestResult.user_id == user_id)
        .order_by(models.TestResult.created_at.desc())
        .limit(5)
        .all()
    )
    if tests:
        t_text = "\n".join([
            f"  - {t.created_at.strftime('%d.%m.%Y')}: {t.total_score} баллов"
            for t in tests
        ])
        parts.append(f"Последние результаты тестов:\n{t_text}")

    return "\n\n".join(parts) if parts else "Нет данных о пользователе."


def ask_ai_assistant(user_id: int, prompt: str, db: Session, chat_history: list = None) -> dict:
    try:
        user_context = _build_user_context(user_id, db)

        # Detect language by the latest user message (prefer chat_history if present)
        detected_lang = None
        if chat_history:
            for m in reversed(chat_history):
                if (m.get("role") or "").strip().lower() == "user" and (m.get("text") or "").strip():
                    detected_lang = _detect_lang(m.get("text") or "")
                    break
        if not detected_lang:
            detected_lang = _detect_lang(prompt or "")

        lang_directive = _lang_instruction(detected_lang)

        system_prompt = f"""Ты профессиональный психологический ассистент.
Твоя задача - помогать пользователям с их психологическим состоянием, давать советы и поддержку.
Ты помнишь весь разговор с пользователем и знаешь всё о его состоянии.
{lang_directive} Будь эмпатичным и профессиональным.

=== Полная информация о работнике ===
{user_context}
=== Конец информации ==="""

        messages = [{"role": "system", "content": system_prompt}]

        # Add previous chat history from this session (normalized)
        messages.extend(_normalize_chat_history(chat_history))

        # Also load recent AI logs as fallback context (previous sessions)
        if not chat_history:
            recent_logs = (
                db.query(models.AILog)
                .filter(models.AILog.user_id == user_id)
                .order_by(models.AILog.created_at.desc())
                .limit(6)
                .all()
            )
            for log in reversed(recent_logs):
                messages.append({"role": "user", "content": log.request})
                messages.append({"role": "assistant", "content": log.response})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=800,
            temperature=0.8
        )

        ai_reply = response.choices[0].message.content

        if not ai_reply or len(ai_reply.strip()) < 5:
            return {"success": False, "response": None, "error": "Invalid GPT response"}

        logger.info(f"AI assistant responded to user {user_id}")
        return {"success": True, "response": ai_reply, "error": None}

    except Exception as e:
        logger.error(f"AI assistant error for user {user_id}: {e}", exc_info=True)
        return {"success": False, "response": None, "error": str(e)}


def explain_question(question_text: str, options: list, lang: str = "ru") -> dict:
    try:
        options_text = "\n".join([f"- {opt['text']} ({opt['points']} points)" for opt in options])

        lang_instructions = {
            "ru": "Отвечай на русском языке.",
            "zh": "请用中文回答。",
        }
        lang_instruction = lang_instructions.get(lang, "Отвечай на русском языке.")

        prompt = f"""Explain this psychological question in simple terms.

Question: {question_text}

Answer options:
{options_text}

Give a brief explanation (3-5 sentences):
- What this question evaluates
- How to understand the answer options
- Advice for honest answering"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a psychological consultant. You help users understand psychological test questions. {lang_instruction}"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )

        result = response.choices[0].message.content

        if not result or len(result.strip()) < 10:
            return {"success": False, "explanation": None, "error": "Invalid GPT response"}

        return {"success": True, "explanation": result, "error": None}

    except Exception as e:
        logger.error(f"AI explain question error: {e}", exc_info=True)
        return {"success": False, "explanation": None, "error": str(e)}


def translate_text(text: str, target_lang: str) -> dict:
    try:
        lang_names = {"zh": "Chinese", "en": "English", "kk": "Kazakh"}
        lang_name = lang_names.get(target_lang, target_lang)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Translate the following text to {lang_name}. Return only the translation, nothing else."},
                {"role": "user", "content": text}
            ],
            max_tokens=200,
            temperature=0.3
        )
        result = response.choices[0].message.content.strip()
        return {"success": True, "text": result}
    except Exception as e:
        logger.error(f"AI translate text error: {e}", exc_info=True)
        return {"success": False, "text": None, "error": str(e)}


def translate_question(question_text: str, options: list, target_lang: str) -> dict:
    try:
        options_text = "\n".join([f'- "{opt["text"]}" ({opt["points"]} points)' for opt in options])

        lang_names = {"zh": "Chinese", "en": "English", "kk": "Kazakh"}
        lang_name = lang_names.get(target_lang, target_lang)

        prompt = f"""Translate the following psychological test question and its answer options to {lang_name}.
Keep the meaning exactly the same. Return ONLY valid JSON with this format:
{{"text": "translated question", "options": [{{"text": "translated option", "points": N}}, ...]}}

Question: {question_text}

Options:
{options_text}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate to {lang_name}. Return only valid JSON, no markdown."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )

        import json
        result_text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        parsed = json.loads(result_text)

        return {"success": True, "text": parsed["text"], "options": parsed["options"]}

    except Exception as e:
        logger.error(f"AI translate question error: {e}", exc_info=True)
        return {"success": False, "text": None, "options": None, "error": str(e)}
