from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import os
import models, auth, database
import schemas
from api import gpt_client
from seed_data import seed_database

models.Base.metadata.create_all(bind=database.engine)

# Auto-seed test data if DB is empty
with database.SessionLocal() as db:
    seed_database(db)

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
@app.get("/materials", response_model=schemas.MaterialsResponse, tags=["materials"])
def list_materials(db: Session = Depends(database.get_db)):
    materials = db.query(models.Material).order_by(models.Material.created_at.desc()).all()
    return {"materials": materials}


@app.post("/materials", tags=["materials"])
def create_material(
        data: schemas.MaterialCreate,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role not in (models.UserRole.therapist, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Only therapists/admin can add materials")

    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Content is required")

    m = models.Material(title=data.title.strip(), content=data.content.strip(), author_id=user.id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"message": "Material created", "material_id": m.id}


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
def log_wellbeing(data: schemas.JournalCreate, user: models.User = Depends(auth.get_current_user),
                  db: Session = Depends(database.get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    if not (0 <= data.score <= 5):
        raise HTTPException(status_code=400, detail="Score must be 0-5")
    entry = models.Journal(wellbeing_score=data.score, note_text=data.note, user_id=user.id)
    db.add(entry)
    db.commit()

    background_tasks.add_task(gpt_client.generate_user_summary, user.id, db)
    return {"status": "success"}


@app.get("/journal", response_model=schemas.JournalsResponse, tags=["journal"])
def get_recent_journals(user: models.User = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    journals = (
        db.query(models.Journal)
        .filter(models.Journal.user_id == user.id)
        .order_by(models.Journal.created_at.desc())
        .limit(5)
        .all()
    )
    return {"message": "Journals fetched", "journals": journals}


@app.delete("/journal/{journal_id}", tags=["journal"])
def delete_journal(journal_id: int, user: models.User = Depends(auth.get_current_user),
                   db: Session = Depends(database.get_db)):
    journal = db.query(models.Journal).filter(models.Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if journal.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this journal entry")

    db.delete(journal)
    db.commit()
    return {"message": "Journal entry deleted"}


# --- TESTS (CRUD) ---
@app.post("/test/create", tags=["testing"])
def create_test(
        data: schemas.TestCreate,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Только терапевты могут создавать тесты")

    new_test = models.Test(title=data.title, description=data.description, therapist_id=user.id)
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return {"message": "Тест создан", "test_id": new_test.id}


@app.get("/tests", tags=["testing"])
def get_tests(
        lang: Optional[str] = Query(None),
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    tests = db.query(models.Test).order_by(models.Test.created_at.desc()).all()
    result = []
    for t in tests:
        title = t.title
        description = t.description

        if lang and lang != "ru":
            cached = db.query(models.TestTranslation).filter(
                models.TestTranslation.test_id == t.id,
                models.TestTranslation.lang == lang
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

    db.delete(test)
    db.commit()
    return {"message": "Тест удалён"}


# --- QUESTIONS ---
@app.post("/test/add-question", tags=["testing"])
def add_question(
        q_data: schemas.QuestionCreate,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Только терапевты могут добавлять вопросы")

    if q_data.test_id:
        test = db.query(models.Test).filter(models.Test.id == q_data.test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Тест не найден")

    options_json = [opt.model_dump() for opt in q_data.options]

    new_q = models.Question(text=q_data.text, options=options_json, test_id=q_data.test_id)
    db.add(new_q)
    db.commit()
    return {"message": "Вопрос успешно добавлен"}


@app.get("/test/questions", response_model=schemas.QuestionsResponse, tags=["testing"])
def get_questions(
        test_id: Optional[int] = Query(None),
        lang: Optional[str] = Query(None),
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    query = db.query(models.Question)
    if test_id is not None:
        query = query.filter(models.Question.test_id == test_id)
    questions = query.all()

    if lang and lang != "ru":
        translated = []
        for q in questions:
            cached = db.query(models.QuestionTranslation).filter(
                models.QuestionTranslation.question_id == q.id,
                models.QuestionTranslation.lang == lang
            ).first()
            if cached:
                translated.append(schemas.QuestionOut(
                    id=q.id, text=cached.translated_text,
                    options=cached.translated_options, test_id=q.test_id
                ))
            else:
                translated.append(q)
        return {"message": "Questions fetched", "questions": translated}

    return {"message": "Questions fetched", "questions": questions}


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

    db.delete(question)
    db.commit()
    return {"message": "Вопрос успешно удалён"}


@app.post("/test/submit", tags=["testing"])
def submit_test(data: schemas.TestSubmit, user: models.User = Depends(auth.get_current_user),
                db: Session = Depends(database.get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
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

    background_tasks.add_task(gpt_client.generate_user_summary, user.id, db)

    return {"message": "Result saved", "total_score": total_score}


@app.get("/test/results", response_model=schemas.TestResultsResponse, tags=["testing"])
def get_my_test_results(
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

        # AI summary
        ai_summary = (
            db.query(models.AISummary)
            .filter(models.AISummary.user_id == w.id)
            .order_by(models.AISummary.created_at.desc())
            .first()
        )

        result.append({
            "id": w.id,
            "full_name": w.full_name,
            "mail": w.mail,
            "test_results": result_list,
            "journals_count": len(journals),
            "avg_score": avg_score,
            "journal_scores": journal_scores,
            "ai_summary": ai_summary.summary_text if ai_summary else None,
        })

    return {"workers": result}


@app.delete("/admin/user/{user_id}", tags=["admin"])
def delete_user(
        user_id: int,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role not in (models.UserRole.therapist, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Not authorized")

    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Cascade delete user data
    db.query(models.Journal).filter(models.Journal.user_id == user_id).delete()
    db.query(models.TestResult).filter(models.TestResult.user_id == user_id).delete()
    db.query(models.AILog).filter(models.AILog.user_id == user_id).delete()
    db.query(models.AISummary).filter(models.AISummary.user_id == user_id).delete()
    db.delete(target)
    db.commit()
    return {"message": "User deleted"}


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
