"""
Auto-seed: populates the database with test data if it's empty.
Called from main.py on startup.
"""
import logging
import random
import models
import auth
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

THERAPIST = {"full_name": "Dr. Anna Petrova", "mail": "anna@test.com", "password": "password123", "role": "therapist"}
WORKERS = [
    {"full_name": "Иван Сидоров", "mail": "ivan@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Maria Chen", "mail": "maria@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Алексей Козлов", "mail": "alexey@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Li Wei", "mail": "liwei@test.com", "password": "password123", "role": "worker"},
]

TESTS = [
    {
        "title": "Тест на уровень стресса",
        "description": "Оцените ваш текущий уровень стресса",
        "questions": [
            {"text": "Как часто вы чувствуете себя напряжённым на работе?", "options": [
                {"text": "Никогда", "points": 1}, {"text": "Редко", "points": 2},
                {"text": "Иногда", "points": 3}, {"text": "Часто", "points": 4}, {"text": "Постоянно", "points": 5}]},
            {"text": "Удаётся ли вам расслабиться после рабочего дня?", "options": [
                {"text": "Всегда легко", "points": 1}, {"text": "Обычно да", "points": 2},
                {"text": "Через некоторое время", "points": 3}, {"text": "С трудом", "points": 4}, {"text": "Практически нет", "points": 5}]},
            {"text": "Как вы оцениваете качество своего сна?", "options": [
                {"text": "Отлично сплю", "points": 1}, {"text": "Хорошо", "points": 2},
                {"text": "Нормально", "points": 3}, {"text": "Плохо", "points": 4}, {"text": "Страдаю бессонницей", "points": 5}]},
            {"text": "Испытываете ли вы тревогу без видимой причины?", "options": [
                {"text": "Нет", "points": 1}, {"text": "Очень редко", "points": 2},
                {"text": "Иногда", "points": 3}, {"text": "Часто", "points": 4}, {"text": "Постоянно", "points": 5}]},
            {"text": "Как часто у вас болит голова или мышцы от напряжения?", "options": [
                {"text": "Никогда", "points": 1}, {"text": "Раз в месяц", "points": 2},
                {"text": "Раз в неделю", "points": 3}, {"text": "Несколько раз в неделю", "points": 4}, {"text": "Каждый день", "points": 5}]},
        ],
    },
    {
        "title": "Шкала эмоционального выгорания",
        "description": "Определите степень эмоционального выгорания",
        "questions": [
            {"text": "Чувствуете ли вы эмоциональное истощение к концу дня?", "options": [
                {"text": "Нет, полон энергии", "points": 1}, {"text": "Немного устаю", "points": 2},
                {"text": "Заметно устаю", "points": 3}, {"text": "Сильно истощён", "points": 4}, {"text": "Полностью выгоревший", "points": 5}]},
            {"text": "Мотивирует ли вас ваша работа?", "options": [
                {"text": "Очень мотивирует", "points": 1}, {"text": "В целом да", "points": 2},
                {"text": "Нейтрально", "points": 3}, {"text": "Скорее нет", "points": 4}, {"text": "Совсем не мотивирует", "points": 5}]},
            {"text": "Как вы относитесь к коллегам?", "options": [
                {"text": "Тепло и дружелюбно", "points": 1}, {"text": "Нормально", "points": 2},
                {"text": "Равнодушно", "points": 3}, {"text": "Раздражённо", "points": 4}, {"text": "Враждебно", "points": 5}]},
            {"text": "Чувствуете ли вы, что ваша работа имеет смысл?", "options": [
                {"text": "Определённо да", "points": 1}, {"text": "Скорее да", "points": 2},
                {"text": "Не уверен", "points": 3}, {"text": "Скорее нет", "points": 4}, {"text": "Точно нет", "points": 5}]},
        ],
    },
    {
        "title": "Тест на удовлетворённость жизнью",
        "description": "Насколько вы удовлетворены различными аспектами жизни",
        "questions": [
            {"text": "Насколько вы удовлетворены своей жизнью в целом?", "options": [
                {"text": "Полностью удовлетворён", "points": 1}, {"text": "В основном да", "points": 2},
                {"text": "Частично", "points": 3}, {"text": "Скорее нет", "points": 4}, {"text": "Совсем не удовлетворён", "points": 5}]},
            {"text": "Есть ли у вас хобби или увлечения вне работы?", "options": [
                {"text": "Да, несколько активных хобби", "points": 1}, {"text": "Одно-два увлечения", "points": 2},
                {"text": "Иногда чем-то занимаюсь", "points": 3}, {"text": "Почти нет времени", "points": 4}, {"text": "Нет никаких увлечений", "points": 5}]},
            {"text": "Как вы оцениваете свои отношения с близкими?", "options": [
                {"text": "Отличные", "points": 1}, {"text": "Хорошие", "points": 2},
                {"text": "Нормальные", "points": 3}, {"text": "Напряжённые", "points": 4}, {"text": "Плохие", "points": 5}]},
        ],
    },
]

WORKER_PROFILES = [
    [0, 1, 0, 1, 1],
    [2, 3, 2, 3, 2],
    [3, 4, 3, 4, 3],
    [1, 2, 1, 0, 2],
]

JOURNAL_NOTES = [
    (4, "Хороший день, чувствую себя бодро"),
    (3, "Обычный день, немного устал"),
    (2, "Тяжёлый день, много стресса"),
    (5, "Отличное настроение!"),
    (1, "Очень плохо себя чувствую"),
    (3, None),
    (4, "Продуктивный день"),
]


def seed_database(db: Session):
    """Populate DB with test data if no users exist."""
    if db.query(models.User).first():
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
    for test_data in TESTS:
        test = models.Test(title=test_data["title"], description=test_data["description"], therapist_id=therapist.id)
        db.add(test)
        db.flush()
        all_tests.append(test)

        for q_data in test_data["questions"]:
            question = models.Question(text=q_data["text"], options=q_data["options"], test_id=test.id)
            db.add(question)
        db.flush()

    # Workers take tests
    for i, worker in enumerate(workers):
        for ti, test in enumerate(all_tests):
            total_score = 0
            for j, question in enumerate(test.questions):
                num_options = len(question.options)
                if ti == 0 and j < len(WORKER_PROFILES[i]):
                    idx = WORKER_PROFILES[i][j]
                else:
                    idx = random.randint(0, num_options - 1)
                total_score += question.options[idx]["points"]

            result = models.TestResult(total_score=total_score, user_id=worker.id, test_id=test.id)
            db.add(result)

        # Journal entries
        for _ in range(random.randint(2, 3)):
            score, note = random.choice(JOURNAL_NOTES)
            entry = models.Journal(wellbeing_score=score, note_text=note, user_id=worker.id)
            db.add(entry)

    db.commit()
    logger.info("Seed data created successfully!")
    logger.info("Therapist: anna@test.com / password123")
    logger.info("Workers: ivan@test.com, maria@test.com, alexey@test.com, liwei@test.com (all password123)")
