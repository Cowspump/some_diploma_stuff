from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import os
import models, auth, database
import schemas
from api import gpt_client
from api.test_translation_tasks import (
    translate_test_task,
    translate_question_task,
    translate_material_task,
    translate_journal_task,
)
from api.lang_detect import detect_ru_en_zh
from seed_data import seed_database
from sqlalchemy import func

models.Base.metadata.create_all(bind=database.engine)

# Миграция: добавляем новые колонки в существующие таблицы
from sqlalchemy import inspect, text

with database.engine.connect() as conn:
    inspector = inspect(database.engine)

    # Добавляем test_id в questions если нет
    if "questions" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("questions")]
        if "test_id" not in columns:
            conn.execute(text("ALTER TABLE questions ADD COLUMN test_id INTEGER REFERENCES tests(id)"))
            conn.commit()

    # Добавляем test_id в test_results если нет
    if "test_results" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("test_results")]
        if "test_id" not in columns:
            conn.execute(text("ALTER TABLE test_results ADD COLUMN test_id INTEGER REFERENCES tests(id)"))
            conn.commit()

    # Добавляем source_lang в materials если нет
    if "materials" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("materials")]
        if "source_lang" not in columns:
            conn.execute(text("ALTER TABLE materials ADD COLUMN source_lang VARCHAR DEFAULT 'ru'"))
            conn.execute(text("UPDATE materials SET source_lang = 'ru' WHERE source_lang IS NULL OR source_lang = ''"))
            conn.commit()
        if "emoji" not in columns:
            conn.execute(text("ALTER TABLE materials ADD COLUMN emoji VARCHAR"))
            conn.commit()

    # Добавляем source_lang в tests если нет
    if "tests" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("tests")]
        if "source_lang" not in columns:
            conn.execute(text("ALTER TABLE tests ADD COLUMN source_lang VARCHAR DEFAULT 'ru'"))
            conn.execute(text("UPDATE tests SET source_lang = 'ru' WHERE source_lang IS NULL OR source_lang = ''"))
            conn.commit()

    # Добавляем source_lang в questions если нет
    if "questions" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("questions")]
        if "source_lang" not in columns:
            conn.execute(text("ALTER TABLE questions ADD COLUMN source_lang VARCHAR DEFAULT 'ru'"))
            conn.execute(text("UPDATE questions SET source_lang = 'ru' WHERE source_lang IS NULL OR source_lang = ''"))
            conn.commit()

    # Добавляем source_lang в journals если нет
    if "journals" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("journals")]
        if "source_lang" not in columns:
            conn.execute(text("ALTER TABLE journals ADD COLUMN source_lang VARCHAR DEFAULT 'ru'"))
            conn.execute(text("UPDATE journals SET source_lang = 'ru' WHERE source_lang IS NULL OR source_lang = ''"))
            conn.commit()

    # Создаём таблицу journal_translations если её нет
    if "journal_translations" not in inspector.get_table_names():
        models.JournalTranslation.__table__.create(bind=conn)

    # Создаём таблицу seed_state если её нет
    if "seed_state" not in inspector.get_table_names():
        models.SeedState.__table__.create(bind=conn)

# Auto-seed test data if DB is empty
with database.SessionLocal() as db:
    seed_database(db)

app = FastAPI(title="Psychology & AI System")

origins = [
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", "*")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- AUTH ---
@app.post("/token", tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # Hardcoded admin access for demo/testing: admin / admin
    if form_data.username == "admin" and form_data.password == "admin":
        user = db.query(models.User).filter(models.User.mail == "admin").first()
        if not user:
            user = models.User(
                full_name="Administrator",
                mail="admin",
                hashed_password=auth.get_password_hash("admin"),
                role=models.UserRole.admin,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif user.role != models.UserRole.admin:
            user.role = models.UserRole.admin
            db.commit()
            db.refresh(user)
    else:
        user = db.query(models.User).filter(models.User.mail == form_data.username).first()
        if not user or not auth.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = auth.create_access_token(data={"sub": user.mail})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.mail,
            "role": user.role.value,
            "fullName": user.full_name,
            "id": user.id
        }
    }


@app.get("/auth/me", tags=["auth"])
def get_current_user_info(user: models.User = Depends(auth.get_current_user)):
    return {
        "email": user.mail,
        "role": user.role.value,
        "fullName": user.full_name,
        "id": user.id
    }


# --- MATERIALS ---
@app.get("/materials", tags=["materials"])
def list_materials(
        lang: Optional[str] = Query(None),
        db: Session = Depends(database.get_db),
):
    # Default requested language is Russian even if query param isn't provided
    requested_lang = (lang or "ru").strip().lower()
    if requested_lang not in ("ru", "en", "zh"):
        requested_lang = "ru"

    materials = db.query(models.Material).order_by(models.Material.created_at.desc()).all()
    result = []
    for m in materials:
        title = m.title
        content = m.content
        emoji = getattr(m, "emoji", None)

        source_lang = (getattr(m, "source_lang", None) or "ru").strip().lower() or "ru"
        if source_lang not in ("ru", "en", "zh"):
            source_lang = "ru"

        # If client requests the original language, never substitute with cached translations.
        if requested_lang != source_lang:
            cached = db.query(models.MaterialTranslation).filter(
                models.MaterialTranslation.material_id == m.id,
                models.MaterialTranslation.lang == requested_lang,
            ).first()
            if cached:
                title = cached.translated_title
                content = cached.translated_content

        result.append({
            "id": m.id,
            "title": title,
            "content": content,
            "emoji": emoji,
            "created_at": m.created_at,
        })
    return {"materials": result}


@app.post("/materials", tags=["materials"])
def create_material(
        data: schemas.MaterialCreate,
        background_tasks: BackgroundTasks,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role not in (models.UserRole.therapist, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Only therapists/admin can add materials")

    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Content is required")

    title = data.title.strip()
    content = data.content.strip()
    source_lang = detect_ru_en_zh(f"{title}\n{content}")

    emoji = (data.emoji or "").strip() or None
    if emoji and len(emoji) > 16:
        raise HTTPException(status_code=400, detail="Emoji is too long")

    m = models.Material(title=title, content=content, emoji=emoji, source_lang=source_lang, author_id=user.id)
    db.add(m)
    db.commit()
    db.refresh(m)

    # Avoid heavy Argos model downloads in the web process; hybrid translator can fallback to LLM.
    background_tasks.add_task(translate_material_task, m.id, auto_install_models=False)
    return {"message": "Material created", "material_id": m.id}


@app.delete("/materials/{material_id}", tags=["materials"])
def delete_material(
        material_id: int,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role not in (models.UserRole.therapist, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Only therapists/admin can delete materials")

    m = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")

    if user.role == models.UserRole.therapist and m.author_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own materials")

    db.query(models.MaterialTranslation).filter(models.MaterialTranslation.material_id == material_id).delete()
    db.delete(m)
    db.commit()
    return {"message": "Material deleted"}


@app.put("/materials/{material_id}", tags=["materials"])
def update_material(
        material_id: int,
        data: schemas.MaterialUpdate,
        background_tasks: BackgroundTasks,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role not in (models.UserRole.therapist, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Only therapists/admin can edit materials")

    m = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")

    if data.title is not None:
        if not data.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        m.title = data.title.strip()
    if data.content is not None:
        if not data.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        m.content = data.content.strip()

    if data.emoji is not None:
        emoji = (data.emoji or "").strip()
        if emoji and len(emoji) > 16:
            raise HTTPException(status_code=400, detail="Emoji is too long")
        m.emoji = (emoji or None)

    # Re-detect source language after any edits
    m.source_lang = detect_ru_en_zh(f"{m.title}\n{m.content}")

    db.commit()
    db.refresh(m)

    background_tasks.add_task(translate_material_task, m.id, auto_install_models=False)
    return {"message": "Material updated", "material_id": m.id}


@app.post("/auth/reset-password", tags=["auth"])
def reset_password(data: schemas.PasswordResetRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.mail == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user.hashed_password = auth.get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@app.post("/register", tags=["auth"])
def register(data: schemas.UserRegister, db: Session = Depends(database.get_db)):
    try:
        user_role = models.UserRole(data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be 'worker', 'therapist' or 'admin'")

    existing_user = db.query(models.User).filter(models.User.mail == data.mail).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = auth.get_password_hash(data.password)
    new_user = models.User(full_name=data.full_name, mail=data.mail, hashed_password=hashed_pwd, role=user_role)
    db.add(new_user)
    db.commit()
    return {"message": "User created"}


# --- JOURNAL ---
@app.post("/journal", tags=["journal"])
def log_wellbeing(
    background_tasks: BackgroundTasks,
    data: schemas.JournalCreate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    if not (0 <= data.score <= 5):
        raise HTTPException(status_code=400, detail="Score must be 0-5")
    note = (data.note or "").strip() or None
    source_lang = detect_ru_en_zh(note or "")
    entry = models.Journal(wellbeing_score=data.score, note_text=note, source_lang=source_lang, user_id=user.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    background_tasks.add_task(gpt_client.generate_user_summaries_task, user.id)
    background_tasks.add_task(translate_journal_task, entry.id, auto_install_models=False)
    return {"status": "success"}


@app.get("/journal", response_model=schemas.JournalsResponse, tags=["journal"])
def get_recent_journals(
    lang: Optional[str] = Query(None),
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    requested_lang = (lang or "ru").strip().lower()
    if requested_lang not in ("ru", "en", "zh"):
        requested_lang = "ru"

    journals = (
        db.query(models.Journal)
        .filter(models.Journal.user_id == user.id)
        .order_by(models.Journal.created_at.desc())
        .limit(5)
        .all()
    )

    if requested_lang != "ru":
        # We'll still translate RU->(others) at display time if needed via cached translations
        pass

    out = []
    for j in journals:
        source_lang = (getattr(j, "source_lang", None) or "ru").strip().lower() or "ru"
        if source_lang not in ("ru", "en", "zh"):
            source_lang = "ru"

        if requested_lang != source_lang and (j.note_text or "").strip():
            cached = (
                db.query(models.JournalTranslation)
                .filter(models.JournalTranslation.journal_id == j.id, models.JournalTranslation.lang == requested_lang)
                .first()
            )
            if cached:
                # return a lightweight object with overridden note_text
                j.note_text = cached.translated_note_text

        out.append(j)

    return {"message": "Journals fetched", "journals": out}


@app.delete("/journal/{journal_id}", tags=["journal"])
def delete_journal(journal_id: int, user: models.User = Depends(auth.get_current_user),
                   db: Session = Depends(database.get_db)):
    journal = db.query(models.Journal).filter(models.Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if journal.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this journal entry")

    db.query(models.JournalTranslation).filter(models.JournalTranslation.journal_id == journal_id).delete(
        synchronize_session=False
    )
    db.delete(journal)
    db.commit()
    return {"message": "Journal entry deleted"}


# --- TESTS (CRUD) ---
@app.post("/test/create", tags=["testing"])
def create_test(
        data: schemas.TestCreate,
        background_tasks: BackgroundTasks,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Только терапевты могут создавать тесты")

    title = (data.title or "").strip()
    description = (data.description or "").strip() if data.description else None
    source_lang = detect_ru_en_zh(f"{title}\n{description or ''}")

    new_test = models.Test(title=title, description=description, source_lang=source_lang, therapist_id=user.id)
    db.add(new_test)
    db.commit()
    db.refresh(new_test)

    # Offline translations (ru->en/zh) stored in DB cache
    background_tasks.add_task(translate_test_task, new_test.id, auto_install_models=False)
    return {"message": "Тест создан", "test_id": new_test.id}


@app.get("/tests", tags=["testing"])
def get_tests(
        lang: Optional[str] = Query(None),
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    requested_lang = (lang or "ru").strip().lower()
    if requested_lang not in ("ru", "en", "zh"):
        requested_lang = "ru"

    tests = db.query(models.Test).order_by(models.Test.created_at.desc()).all()
    result = []
    for t in tests:
        title = t.title
        description = t.description

        source_lang = (getattr(t, "source_lang", None) or "ru").strip().lower() or "ru"
        if source_lang not in ("ru", "en", "zh"):
            source_lang = "ru"

        # If client requests the original language, never substitute with cached translations.
        if requested_lang != source_lang:
            cached = db.query(models.TestTranslation).filter(
                models.TestTranslation.test_id == t.id,
                models.TestTranslation.lang == requested_lang
            ).first()
            if cached:
                title = cached.translated_title
                description = cached.translated_description

        result.append({
            "id": t.id,
            "title": title,
            "description": description,
            "created_at": t.created_at,
            "question_count": len(t.questions)
        })
    return {"message": "Tests fetched", "tests": result}


@app.delete("/test/{test_id}", tags=["testing"])
def delete_test(
        test_id: int,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Только терапевты могут удалять тесты")

    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    if test.therapist_id != user.id:
        raise HTTPException(status_code=403, detail="Можно удалять только свои тесты")

    db.query(models.TestResult).filter(models.TestResult.test_id == test_id).delete(synchronize_session=False)
    question_ids = [qid for (qid,) in db.query(models.Question.id).filter(models.Question.test_id == test_id).all()]
    if question_ids:
        db.query(models.QuestionTranslation).filter(
            models.QuestionTranslation.question_id.in_(question_ids)
        ).delete(synchronize_session=False)
    db.query(models.TestTranslation).filter(models.TestTranslation.test_id == test_id).delete(synchronize_session=False)
    db.query(models.Question).filter(models.Question.test_id == test_id).delete(synchronize_session=False)
    db.delete(test)
    db.commit()
    return {"message": "Тест удалён"}


# --- QUESTIONS ---
@app.post("/test/add-question", tags=["testing"])
def add_question(
        q_data: schemas.QuestionCreate,
        background_tasks: BackgroundTasks,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Только терапевты могут добавлять вопросы")

    if q_data.test_id:
        test = db.query(models.Test).filter(models.Test.id == q_data.test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Тест не найден")

    options_json = [opt.model_dump() for opt in q_data.options]

    q_text = (q_data.text or "").strip()
    opt_texts = "\n".join([(o.get("text") or "") for o in options_json if isinstance(o, dict)])
    source_lang = detect_ru_en_zh(f"{q_text}\n{opt_texts}")

    new_q = models.Question(text=q_text, options=options_json, source_lang=source_lang, test_id=q_data.test_id)
    db.add(new_q)
    db.commit()
    db.refresh(new_q)

    background_tasks.add_task(translate_question_task, new_q.id, auto_install_models=False)
    return {"message": "Вопрос успешно добавлен"}


@app.get("/test/questions", response_model=schemas.QuestionsResponse, tags=["testing"])
def get_questions(
        test_id: Optional[int] = Query(None),
        lang: Optional[str] = Query(None),
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    requested_lang = (lang or "ru").strip().lower()
    if requested_lang not in ("ru", "en", "zh"):
        requested_lang = "ru"

    query = db.query(models.Question)
    if test_id is not None:
        query = query.filter(models.Question.test_id == test_id)
    questions = query.all()

    translated = []
    for q in questions:
        source_lang = (getattr(q, "source_lang", None) or "ru").strip().lower() or "ru"
        if source_lang not in ("ru", "en", "zh"):
            source_lang = "ru"

        if requested_lang == source_lang:
            translated.append(q)
            continue

        cached = db.query(models.QuestionTranslation).filter(
            models.QuestionTranslation.question_id == q.id,
            models.QuestionTranslation.lang == requested_lang
        ).first()
        if cached:
            translated.append(
                schemas.QuestionOut(
                    id=q.id,
                    text=cached.translated_text,
                    options=cached.translated_options,
                    test_id=q.test_id,
                )
            )
        else:
            translated.append(q)
    return {"message": "Questions fetched", "questions": translated}


@app.delete("/test/question/{question_id}", tags=["testing"])
def delete_question(
        question_id: int,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Только терапевты могут удалять вопросы")

    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    if question.test_id is not None:
        owning = db.query(models.Test).filter(models.Test.id == question.test_id).first()
        if not owning or owning.therapist_id != user.id:
            raise HTTPException(status_code=403, detail="Можно удалять вопросы только из своих тестов")

    db.query(models.QuestionTranslation).filter(
        models.QuestionTranslation.question_id == question_id
    ).delete(synchronize_session=False)
    db.delete(question)
    db.commit()
    return {"message": "Вопрос успешно удалён"}


@app.post("/test/submit", tags=["testing"])
def submit_test(
        data: schemas.TestSubmit,
        background_tasks: BackgroundTasks,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role != models.UserRole.worker:
        raise HTTPException(status_code=403, detail="Only workers can submit tests")

    total_score = 0
    for question_id, option_index in data.answers.items():
        question = db.query(models.Question).filter(models.Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=400, detail=f"Question {question_id} not found")

        if option_index < 0 or option_index >= len(question.options):
            raise HTTPException(status_code=400, detail=f"Invalid option index for question {question_id}")

        total_score += question.options[option_index]["points"]

    result = models.TestResult(total_score=total_score, user_id=user.id, test_id=data.test_id)
    db.add(result)
    db.commit()

    background_tasks.add_task(gpt_client.generate_user_summaries_task, user.id)

    return {"message": "Result saved", "total_score": total_score}


@app.get("/test/results", response_model=schemas.TestResultsResponse, tags=["testing"])
def get_my_test_results(
        lang: Optional[str] = Query(None),
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.worker:
        raise HTTPException(status_code=403, detail="Only workers can view their test results")

    results = (
        db.query(models.TestResult)
        .filter(models.TestResult.user_id == user.id)
        .order_by(models.TestResult.created_at.desc())
        .all()
    )

    result_list = []
    for r in results:
        test_title = None
        if r.test_id:
            test = db.query(models.Test).filter(models.Test.id == r.test_id).first()
            if test:
                test_title = test.title
                if lang and lang != "ru":
                    cached = db.query(models.TestTranslation).filter(
                        models.TestTranslation.test_id == test.id,
                        models.TestTranslation.lang == lang
                    ).first()
                    if cached and cached.translated_title:
                        test_title = cached.translated_title
        result_list.append({
            "id": r.id,
            "total_score": r.total_score,
            "created_at": r.created_at,
            "test_id": r.test_id,
            "test_title": test_title
        })

    return {"message": "Results fetched", "results": result_list}


# --- THERAPIST: VIEW WORKERS ---
@app.get("/therapist/workers", tags=["therapist"])
def get_workers(
        lang: Optional[str] = Query(None),
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Only therapists can view workers")

    workers = db.query(models.User).filter(models.User.role == models.UserRole.worker).all()
    result = []
    for w in workers:
        test_results = (
            db.query(models.TestResult)
            .filter(models.TestResult.user_id == w.id)
            .order_by(models.TestResult.created_at.desc())
            .all()
        )
        journals = (
            db.query(models.Journal)
            .filter(models.Journal.user_id == w.id)
            .order_by(models.Journal.created_at.desc())
            .all()
        )

        result_list = []
        total_score = 0
        for r in test_results:
            test_title = None
            if r.test_id:
                test = db.query(models.Test).filter(models.Test.id == r.test_id).first()
                if test:
                    test_title = test.title
            result_list.append({
                "id": r.id,
                "total_score": r.total_score,
                "created_at": r.created_at,
                "test_id": r.test_id,
                "test_title": test_title
            })
            total_score += r.total_score

        avg_score = round(total_score / len(test_results), 1) if test_results else None

        # Journal scores (without note text) for analytics
        journal_scores = [
            {"score": j.wellbeing_score, "date": j.created_at}
            for j in journals
        ]

        # AI summary (pre-generated per lang; fallback to ru, then legacy table)
        requested_lang = lang or "ru"
        preferred = (
            db.query(models.AISummaryTranslation)
            .filter(models.AISummaryTranslation.user_id == w.id, models.AISummaryTranslation.lang == requested_lang)
            .order_by(models.AISummaryTranslation.created_at.desc())
            .first()
        )
        if not preferred and requested_lang != "ru":
            preferred = (
                db.query(models.AISummaryTranslation)
                .filter(models.AISummaryTranslation.user_id == w.id, models.AISummaryTranslation.lang == "ru")
                .order_by(models.AISummaryTranslation.created_at.desc())
                .first()
            )
        summary_text = preferred.summary_text if preferred else None
        if not summary_text:
            legacy = (
                db.query(models.AISummary)
                .filter(models.AISummary.user_id == w.id)
                .order_by(models.AISummary.created_at.desc())
                .first()
            )
            summary_text = legacy.summary_text if legacy else None

        result.append({
            "id": w.id,
            "full_name": w.full_name,
            "mail": w.mail,
            "test_results": result_list,
            "journals_count": len(journals),
            "avg_score": avg_score,
            "journal_scores": journal_scores,
            "ai_summary": summary_text,
        })

    return {"workers": result}


@app.post("/therapist/worker/{worker_id}/regenerate-summary", tags=["therapist"])
def regenerate_worker_summary(
        worker_id: int,
        background_tasks: BackgroundTasks,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Only therapists can regenerate summaries")
    worker = db.query(models.User).filter(models.User.id == worker_id, models.User.role == models.UserRole.worker).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    background_tasks.add_task(gpt_client.generate_user_summaries_task, worker_id)
    return {"message": "Summary regeneration started"}


@app.delete("/admin/user/{user_id}", tags=["admin"])
def delete_user(
        user_id: int,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Cascade delete user data (child rows with FKs must go first)
    journal_ids = [jid for (jid,) in db.query(models.Journal.id).filter(models.Journal.user_id == user_id).all()]
    if journal_ids:
        db.query(models.JournalTranslation).filter(
            models.JournalTranslation.journal_id.in_(journal_ids)
        ).delete(synchronize_session=False)
    db.query(models.Journal).filter(models.Journal.user_id == user_id).delete(synchronize_session=False)
    db.query(models.TestResult).filter(models.TestResult.user_id == user_id).delete(synchronize_session=False)
    db.query(models.AILog).filter(models.AILog.user_id == user_id).delete(synchronize_session=False)
    db.query(models.AISummary).filter(models.AISummary.user_id == user_id).delete(synchronize_session=False)
    db.query(models.AISummaryTranslation).filter(
        models.AISummaryTranslation.user_id == user_id
    ).delete(synchronize_session=False)
    db.delete(target)
    db.commit()
    return {"message": "User deleted"}


@app.get("/admin/users", response_model=schemas.AdminUsersResponse, tags=["admin"])
def admin_list_users(
        role: Optional[str] = Query(None),
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    query = db.query(models.User)
    if role:
        try:
            query = query.filter(models.User.role == models.UserRole(role))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role filter")

    users = query.order_by(models.User.id.desc()).all()

    # Precompute counts
    journal_counts = dict(
        db.query(models.Journal.user_id, func.count(models.Journal.id))
        .group_by(models.Journal.user_id)
        .all()
    )
    result_counts = dict(
        db.query(models.TestResult.user_id, func.count(models.TestResult.id))
        .group_by(models.TestResult.user_id)
        .all()
    )
    tests_created_counts = dict(
        db.query(models.Test.therapist_id, func.count(models.Test.id))
        .group_by(models.Test.therapist_id)
        .all()
    )
    materials_counts = dict(
        db.query(models.Material.author_id, func.count(models.Material.id))
        .group_by(models.Material.author_id)
        .all()
    )

    out = []
    for u in users:
        out.append(
            schemas.AdminUserOut(
                id=u.id,
                full_name=u.full_name,
                mail=u.mail,
                role=u.role.value,
                journals_count=int(journal_counts.get(u.id, 0) or 0),
                test_results_count=int(result_counts.get(u.id, 0) or 0),
                tests_created_count=int(tests_created_counts.get(u.id, 0) or 0),
                materials_count=int(materials_counts.get(u.id, 0) or 0),
            )
        )

    return {"users": out}


@app.delete("/admin/therapist/{therapist_id}", tags=["admin"])
def admin_delete_therapist(
        therapist_id: int,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    target = db.query(models.User).filter(models.User.id == therapist_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role != models.UserRole.therapist:
        raise HTTPException(status_code=400, detail="Target is not a therapist")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Collect tests/questions created by therapist
    test_ids = [t.id for t in db.query(models.Test.id).filter(models.Test.therapist_id == therapist_id).all()]
    if test_ids:
        db.query(models.TestResult).filter(models.TestResult.test_id.in_(test_ids)).delete(synchronize_session=False)
        question_ids = [q.id for q in db.query(models.Question.id).filter(models.Question.test_id.in_(test_ids)).all()]
        if question_ids:
            db.query(models.QuestionTranslation).filter(models.QuestionTranslation.question_id.in_(question_ids)).delete(synchronize_session=False)
        db.query(models.TestTranslation).filter(models.TestTranslation.test_id.in_(test_ids)).delete(synchronize_session=False)

        # Delete questions and tests (questions have delete-orphan cascade from Test, but we delete explicitly for clarity)
        db.query(models.Question).filter(models.Question.test_id.in_(test_ids)).delete(synchronize_session=False)
        db.query(models.Test).filter(models.Test.id.in_(test_ids)).delete(synchronize_session=False)

    # Delete therapist's materials (translations reference materials)
    material_ids = [mid for (mid,) in db.query(models.Material.id).filter(models.Material.author_id == therapist_id).all()]
    if material_ids:
        db.query(models.MaterialTranslation).filter(
            models.MaterialTranslation.material_id.in_(material_ids)
        ).delete(synchronize_session=False)
    db.query(models.Material).filter(models.Material.author_id == therapist_id).delete(synchronize_session=False)

    # Delete therapist's own journals/results/logs/summaries
    t_journal_ids = [jid for (jid,) in db.query(models.Journal.id).filter(models.Journal.user_id == therapist_id).all()]
    if t_journal_ids:
        db.query(models.JournalTranslation).filter(
            models.JournalTranslation.journal_id.in_(t_journal_ids)
        ).delete(synchronize_session=False)
    db.query(models.Journal).filter(models.Journal.user_id == therapist_id).delete(synchronize_session=False)
    db.query(models.TestResult).filter(models.TestResult.user_id == therapist_id).delete(synchronize_session=False)
    db.query(models.AILog).filter(models.AILog.user_id == therapist_id).delete(synchronize_session=False)
    db.query(models.AISummary).filter(models.AISummary.user_id == therapist_id).delete(synchronize_session=False)
    db.query(models.AISummaryTranslation).filter(models.AISummaryTranslation.user_id == therapist_id).delete(synchronize_session=False)

    db.delete(target)
    db.commit()
    return {"message": "Therapist deleted"}


@app.get("/admin/stats", response_model=schemas.AdminStatsResponse, tags=["admin"])
def admin_stats(
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    users_total = db.query(models.User).count()
    users_workers = db.query(models.User).filter(models.User.role == models.UserRole.worker).count()
    users_therapists = db.query(models.User).filter(models.User.role == models.UserRole.therapist).count()
    users_admins = db.query(models.User).filter(models.User.role == models.UserRole.admin).count()

    tests_total = db.query(models.Test).count()
    questions_total = db.query(models.Question).count()
    test_results_total = db.query(models.TestResult).count()
    journals_total = db.query(models.Journal).count()
    materials_total = db.query(models.Material).count()

    return {
        "counts": schemas.AdminStatsCounts(
            users_total=users_total,
            users_workers=users_workers,
            users_therapists=users_therapists,
            users_admins=users_admins,
            tests_total=tests_total,
            questions_total=questions_total,
            test_results_total=test_results_total,
            journals_total=journals_total,
            materials_total=materials_total,
        )
    }


@app.delete("/admin/material/{material_id}", tags=["admin"])
def admin_delete_material(
        material_id: int,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    m = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")

    db.query(models.MaterialTranslation).filter(models.MaterialTranslation.material_id == material_id).delete(
        synchronize_session=False
    )
    db.delete(m)
    db.commit()
    return {"message": "Material deleted"}


# --- AI ASSISTANT ---
@app.post("/ai/ask", tags=["ai"])
async def ai_ask(data: schemas.AIAsk, user: models.User = Depends(auth.get_current_user),
                 db: Session = Depends(database.get_db)):
    history = [{"role": m.role, "text": m.text} for m in (data.chat_history or [])]
    result = gpt_client.ask_ai_assistant(user.id, data.prompt, db, chat_history=history)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"AI service error: {result['error']}")

    ai_reply = result["response"]

    log = models.AILog(user_id=user.id, request=data.prompt, response=ai_reply)
    db.add(log)
    db.commit()

    return {"response": ai_reply}


@app.get("/ai/summary", tags=["ai"])
def get_ai_summary(
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    summary = (
        db.query(models.AISummary)
        .filter(models.AISummary.user_id == user.id)
        .order_by(models.AISummary.created_at.desc())
        .first()
    )
    if not summary:
        return {"summary": None}
    return {
        "summary": {
            "id": summary.id,
            "summary_text": summary.summary_text,
            "created_at": summary.created_at
        }
    }


@app.get("/ai/chat-history", response_model=schemas.AIChatHistoryResponse, tags=["ai"])
def get_ai_chat_history(
        limit: int = Query(50, ge=1, le=200),
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    logs = (
        db.query(models.AILog)
        .filter(models.AILog.user_id == user.id)
        .order_by(models.AILog.created_at.desc())
        .limit(limit)
        .all()
    )
    # return chronological order
    logs = list(reversed(logs))
    return {"history": logs}


@app.post("/ai/explain-question", tags=["ai"])
def explain_question(
        data: schemas.ExplainQuestionRequest,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    question = db.query(models.Question).filter(models.Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    result = gpt_client.explain_question(question.text, question.options, lang=data.lang)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"AI service error: {result['error']}")

    return {"explanation": result["explanation"]}
