from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OptionCreate(BaseModel):
    text: str
    points: int


class QuestionCreate(BaseModel):
    text: str
    options: List[OptionCreate]
    test_id: Optional[int] = None


class OptionOut(BaseModel):
    text: str
    points: int


class QuestionOut(BaseModel):
    id: int
    text: str
    options: List[OptionOut]
    test_id: Optional[int] = None

    class Config:
        from_attributes = True


class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TestOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    question_count: Optional[int] = 0

    class Config:
        from_attributes = True


class TestsResponse(BaseModel):
    message: str
    tests: List[TestOut]


class TestSubmit(BaseModel):
    answers: dict[int, int]  # {question_id: selected_option_index}
    test_id: Optional[int] = None


class TestResultOut(BaseModel):
    id: int
    total_score: int
    created_at: datetime
    test_id: Optional[int] = None
    test_title: Optional[str] = None

    class Config:
        from_attributes = True


class TestResultsResponse(BaseModel):
    message: str
    results: List[TestResultOut]


class QuestionsResponse(BaseModel):
    message: str
    questions: List[QuestionOut]


class JournalOut(BaseModel):
    id: int
    wellbeing_score: int
    note_text: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class JournalsResponse(BaseModel):
    message: str
    journals: List[JournalOut]


class UserRegister(BaseModel):
    full_name: str
    mail: str
    password: str
    role: str


class ChatMessage(BaseModel):
    role: str  # "user" or "ai"
    text: str


class AIAsk(BaseModel):
    prompt: str
    chat_history: Optional[List[ChatMessage]] = None


class AIChatLogOut(BaseModel):
    id: int
    request: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True


class AIChatHistoryResponse(BaseModel):
    history: List[AIChatLogOut]


class JournalCreate(BaseModel):
    score: int
    note: str = None


class AISummaryOut(BaseModel):
    id: int
    summary_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExplainQuestionRequest(BaseModel):
    question_id: int
    lang: Optional[str] = "ru"


class PasswordResetRequest(BaseModel):
    email: str
    new_password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    mail: str
    role: str

    class Config:
        from_attributes = True


class UserWithResults(BaseModel):
    id: int
    full_name: str
    mail: str
    test_results: List[TestResultOut]
    journals_count: int
    avg_score: Optional[float] = None


class MaterialCreate(BaseModel):
    title: str
    content: str
    emoji: Optional[str] = None


class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    emoji: Optional[str] = None


class MaterialOut(BaseModel):
    id: int
    title: str
    content: str
    emoji: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MaterialsResponse(BaseModel):
    materials: List[MaterialOut]


# --- ADMIN ---
class AdminUserOut(BaseModel):
    id: int
    full_name: str
    mail: str
    role: str
    journals_count: int = 0
    test_results_count: int = 0
    tests_created_count: int = 0
    materials_count: int = 0


class AdminUsersResponse(BaseModel):
    users: List[AdminUserOut]


class AdminStatsCounts(BaseModel):
    users_total: int
    users_workers: int
    users_therapists: int
    users_admins: int
    tests_total: int
    questions_total: int
    test_results_total: int
    journals_total: int
    materials_total: int


class AdminStatsResponse(BaseModel):
    counts: AdminStatsCounts
