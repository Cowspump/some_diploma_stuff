from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime


class UserRole(str, enum.Enum):
    worker = "worker"
    therapist = "therapist"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    mail = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.worker)

    journals = relationship("Journal", back_populates="owner")
    test_results = relationship("TestResult", back_populates="user")


class Journal(Base):
    __tablename__ = "journals"
    id = Column(Integer, primary_key=True, index=True)
    wellbeing_score = Column(Integer)
    note_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="journals")


class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    therapist_id = Column(Integer, ForeignKey("users.id"))

    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    results = relationship("TestResult", back_populates="test")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    text = Column(String)
    options = Column(JSON)  # [{'text': 'Хорошо', 'points': 5}, ...]
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)

    test = relationship("Test", back_populates="questions")


class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True)
    total_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)

    user = relationship("User", back_populates="test_results")
    test = relationship("Test", back_populates="results")


class AILog(Base):
    __tablename__ = "ai_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    request = Column(String)
    response = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class AISummary(Base):
    __tablename__ = "ai_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    summary_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuestionTranslation(Base):
    __tablename__ = "question_translations"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    lang = Column(String, nullable=False)
    translated_text = Column(String, nullable=False)
    translated_options = Column(JSON, nullable=False)


class TestTranslation(Base):
    __tablename__ = "test_translations"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    lang = Column(String, nullable=False)
    translated_title = Column(String, nullable=False)
    translated_description = Column(String, nullable=True)
