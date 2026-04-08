"""
Seed script: creates test users, tests with questions, and submits test answers.
Run: python seed.py (from backend/ directory, with the server running at localhost:8000)
"""
import requests
import random

BASE = "http://localhost:8000"

# --- Users to create ---
THERAPIST = {"full_name": "Dr. Anna Petrova", "mail": "anna@test.com", "password": "password123", "role": "therapist"}
WORKERS = [
    {"full_name": "Иван Сидоров", "mail": "ivan@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Maria Chen", "mail": "maria@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Алексей Козлов", "mail": "alexey@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Li Wei", "mail": "liwei@test.com", "password": "password123", "role": "worker"},
]

# --- Tests with questions ---
TESTS = [
    {
        "title": "Тест на уровень стресса",
        "description": "Оцените ваш текущий уровень стресса",
        "questions": [
            {
                "text": "Как часто вы чувствуете себя напряжённым на работе?",
                "options": [
                    {"text": "Никогда", "points": 1},
                    {"text": "Редко", "points": 2},
                    {"text": "Иногда", "points": 3},
                    {"text": "Часто", "points": 4},
                    {"text": "Постоянно", "points": 5},
                ],
            },
            {
                "text": "Удаётся ли вам расслабиться после рабочего дня?",
                "options": [
                    {"text": "Всегда легко", "points": 1},
                    {"text": "Обычно да", "points": 2},
                    {"text": "Через некоторое время", "points": 3},
                    {"text": "С трудом", "points": 4},
                    {"text": "Практически нет", "points": 5},
                ],
            },
            {
                "text": "Как вы оцениваете качество своего сна?",
                "options": [
                    {"text": "Отлично сплю", "points": 1},
                    {"text": "Хорошо", "points": 2},
                    {"text": "Нормально", "points": 3},
                    {"text": "Плохо", "points": 4},
                    {"text": "Страдаю бессонницей", "points": 5},
                ],
            },
            {
                "text": "Испытываете ли вы тревогу без видимой причины?",
                "options": [
                    {"text": "Нет", "points": 1},
                    {"text": "Очень редко", "points": 2},
                    {"text": "Иногда", "points": 3},
                    {"text": "Часто", "points": 4},
                    {"text": "Постоянно", "points": 5},
                ],
            },
            {
                "text": "Как часто у вас болит голова или мышцы от напряжения?",
                "options": [
                    {"text": "Никогда", "points": 1},
                    {"text": "Раз в месяц", "points": 2},
                    {"text": "Раз в неделю", "points": 3},
                    {"text": "Несколько раз в неделю", "points": 4},
                    {"text": "Каждый день", "points": 5},
                ],
            },
        ],
    },
    {
        "title": "Шкала эмоционального выгорания",
        "description": "Определите степень эмоционального выгорания",
        "questions": [
            {
                "text": "Чувствуете ли вы эмоциональное истощение к концу дня?",
                "options": [
                    {"text": "Нет, полон энергии", "points": 1},
                    {"text": "Немного устаю", "points": 2},
                    {"text": "Заметно устаю", "points": 3},
                    {"text": "Сильно истощён", "points": 4},
                    {"text": "Полностью выгоревший", "points": 5},
                ],
            },
            {
                "text": "Мотивирует ли вас ваша работа?",
                "options": [
                    {"text": "Очень мотивирует", "points": 1},
                    {"text": "В целом да", "points": 2},
                    {"text": "Нейтрально", "points": 3},
                    {"text": "Скорее нет", "points": 4},
                    {"text": "Совсем не мотивирует", "points": 5},
                ],
            },
            {
                "text": "Как вы относитесь к коллегам?",
                "options": [
                    {"text": "Тепло и дружелюбно", "points": 1},
                    {"text": "Нормально", "points": 2},
                    {"text": "Равнодушно", "points": 3},
                    {"text": "Раздражённо", "points": 4},
                    {"text": "Враждебно", "points": 5},
                ],
            },
            {
                "text": "Чувствуете ли вы, что ваша работа имеет смысл?",
                "options": [
                    {"text": "Определённо да", "points": 1},
                    {"text": "Скорее да", "points": 2},
                    {"text": "Не уверен", "points": 3},
                    {"text": "Скорее нет", "points": 4},
                    {"text": "Точно нет", "points": 5},
                ],
            },
        ],
    },
    {
        "title": "Тест на удовлетворённость жизнью",
        "description": "Насколько вы удовлетворены различными аспектами жизни",
        "questions": [
            {
                "text": "Насколько вы удовлетворены своей жизнью в целом?",
                "options": [
                    {"text": "Полностью удовлетворён", "points": 1},
                    {"text": "В основном да", "points": 2},
                    {"text": "Частично", "points": 3},
                    {"text": "Скорее нет", "points": 4},
                    {"text": "Совсем не удовлетворён", "points": 5},
                ],
            },
            {
                "text": "Есть ли у вас хобби или увлечения вне работы?",
                "options": [
                    {"text": "Да, несколько активных хобби", "points": 1},
                    {"text": "Одно-два увлечения", "points": 2},
                    {"text": "Иногда чем-то занимаюсь", "points": 3},
                    {"text": "Почти нет времени", "points": 4},
                    {"text": "Нет никаких увлечений", "points": 5},
                ],
            },
            {
                "text": "Как вы оцениваете свои отношения с близкими?",
                "options": [
                    {"text": "Отличные", "points": 1},
                    {"text": "Хорошие", "points": 2},
                    {"text": "Нормальные", "points": 3},
                    {"text": "Напряжённые", "points": 4},
                    {"text": "Плохие", "points": 5},
                ],
            },
        ],
    },
]

# Worker answer profiles (tendency: low stress, medium, high, mixed)
WORKER_PROFILES = [
    [0, 1, 0, 1, 1],   # Ivan - low stress
    [2, 3, 2, 3, 2],   # Maria - medium-high
    [3, 4, 3, 4, 3],   # Alexey - high stress
    [1, 2, 1, 0, 2],   # Li Wei - low-medium
]


def login(email, password):
    r = requests.post(f"{BASE}/token", data={"username": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def register(user):
    r = requests.post(f"{BASE}/register", json=user)
    if r.status_code == 400 and "already registered" in r.text:
        print(f"  User {user['mail']} already exists, skipping")
        return
    r.raise_for_status()
    print(f"  Created user: {user['full_name']} ({user['role']})")


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def main():
    print("=== Registering users ===")
    register(THERAPIST)
    for w in WORKERS:
        register(w)

    print("\n=== Creating tests (as therapist) ===")
    therapist_token = login(THERAPIST["mail"], THERAPIST["password"])
    headers = auth_headers(therapist_token)

    test_ids = []
    for test_data in TESTS:
        r = requests.post(f"{BASE}/test/create", json={"title": test_data["title"], "description": test_data["description"]}, headers=headers)
        r.raise_for_status()
        test_id = r.json()["test_id"]
        test_ids.append(test_id)
        print(f"  Created test: {test_data['title']} (id={test_id})")

        for q in test_data["questions"]:
            r = requests.post(f"{BASE}/test/add-question", json={"text": q["text"], "options": q["options"], "test_id": test_id}, headers=headers)
            r.raise_for_status()
        print(f"    Added {len(test_data['questions'])} questions")

    print("\n=== Fetching question IDs ===")
    # Get questions per test
    test_questions = {}
    for tid in test_ids:
        r = requests.get(f"{BASE}/test/questions?test_id={tid}", headers=headers)
        r.raise_for_status()
        test_questions[tid] = r.json()["questions"]
        print(f"  Test {tid}: {len(test_questions[tid])} questions")

    print("\n=== Workers taking tests ===")
    for i, worker in enumerate(WORKERS):
        token = login(worker["mail"], worker["password"])
        wh = auth_headers(token)

        for tid in test_ids:
            questions = test_questions[tid]
            answers = {}
            for j, q in enumerate(questions):
                num_options = len(q["options"])
                # Use profile for first test, randomize slightly for others
                if tid == test_ids[0] and j < len(WORKER_PROFILES[i]):
                    idx = WORKER_PROFILES[i][j]
                else:
                    idx = random.randint(0, num_options - 1)
                answers[str(q["id"])] = idx

            r = requests.post(f"{BASE}/test/submit", json={"answers": answers, "test_id": tid}, headers=wh)
            r.raise_for_status()
            score = r.json()["total_score"]
            print(f"  {worker['full_name']} completed test {tid}, score: {score}")

    # Also add some journal entries for workers
    print("\n=== Adding journal entries ===")
    journal_notes = [
        (4, "Хороший день, чувствую себя бодро"),
        (3, "Обычный день, немного устал"),
        (2, "Тяжёлый день, много стресса"),
        (5, "Отличное настроение!"),
        (1, "Очень плохо себя чувствую"),
        (3, None),
        (4, "Продуктивный день"),
    ]

    for i, worker in enumerate(WORKERS):
        token = login(worker["mail"], worker["password"])
        wh = auth_headers(token)
        # Each worker gets 2-3 random journal entries
        for _ in range(random.randint(2, 3)):
            score, note = random.choice(journal_notes)
            payload = {"score": score}
            if note:
                payload["note"] = note
            r = requests.post(f"{BASE}/journal", json=payload, headers=wh)
            r.raise_for_status()
        print(f"  Added journals for {worker['full_name']}")

    print("\n=== Done! ===")
    print("Therapist login: anna@test.com / password123")
    print("Worker logins: ivan@test.com, maria@test.com, alexey@test.com, liwei@test.com (all password123)")


if __name__ == "__main__":
    main()
