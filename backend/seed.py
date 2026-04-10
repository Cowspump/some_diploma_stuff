"""
Seed script: creates test users, tests with questions, and submits test answers.
Run: python seed.py (from backend/ directory, with the server running at localhost:8000)
"""
import requests

BASE = "http://localhost:8000"

# --- Users to create ---
THERAPIST = {"full_name": "Dr. Anna Petrova", "mail": "anna@test.com", "password": "password123", "role": "therapist"}
WORKERS = [
    {"full_name": "Иван Сидоров", "mail": "ivan@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Maria Chen", "mail": "maria@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Алексей Козлов", "mail": "alexey@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Li Wei", "mail": "liwei@test.com", "password": "password123", "role": "worker"},
]

# NOTE:
# Canonical seed data (tests/materials/results/journals, including dated data and translations)
# is created by the auto-seed in backend/src/seed_data.py.


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
    print("\n=== Done! ===")
    print("Users ensured. Tests/materials/results/journals are seeded by backend/src/seed_data.py on app startup.")
    print("Therapist login: anna@test.com / password123")
    print("Worker logins: ivan@test.com, maria@test.com, alexey@test.com, liwei@test.com (all password123)")


if __name__ == "__main__":
    main()
