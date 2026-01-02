"""Database models for the English Learning Bot"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    create_engine,
    String,
    Integer,
    BigInteger,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class User(Base):
    """User model - stores Telegram user information and preferences"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # User preferences
    daily_word_limit: Mapped[int] = mapped_column(Integer, default=10)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_time: Mapped[Optional[str]] = mapped_column(String(5), default="09:00")  # HH:MM format
    
    # Tracking
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    word_progress: Mapped[list["UserWordProgress"]] = relationship(
        "UserWordProgress", back_populates="user", cascade="all, delete-orphan"
    )
    study_sessions: Mapped[list["StudySession"]] = relationship(
        "StudySession", back_populates="user", cascade="all, delete-orphan"
    )
    added_words: Mapped[list["Word"]] = relationship(
        "Word", back_populates="added_by_user", foreign_keys="Word.added_by"
    )
    word_edits: Mapped[list["WordEditHistory"]] = relationship(
        "WordEditHistory", back_populates="edited_by_user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Word(Base):
    """Word model - stores English words with definitions and examples"""
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    example: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translation: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Metadata
    added_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    added_by_user: Mapped["User"] = relationship("User", back_populates="added_words", foreign_keys=[added_by])
    user_progress: Mapped[list["UserWordProgress"]] = relationship(
        "UserWordProgress", back_populates="word", cascade="all, delete-orphan"
    )
    edit_history: Mapped[list["WordEditHistory"]] = relationship(
        "WordEditHistory", back_populates="word", cascade="all, delete-orphan"
    )
    
    # Ensure unique words (case-insensitive)
    __table_args__ = (
        UniqueConstraint('word', name='uq_word_lowercase'),
        Index('idx_word_lower', 'word'),
    )

    def __repr__(self):
        return f"<Word(id={self.id}, word={self.word})>"


class UserWordProgress(Base):
    """Tracks individual user's progress with each word using Leitner system"""
    __tablename__ = "user_word_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id"), nullable=False)
    
    # Leitner box system (1-7)
    leitner_box: Mapped[int] = mapped_column(Integer, default=1)
    
    # Difficulty rating by user
    difficulty: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # easy, normal, hard
    
    # Review tracking
    times_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_incorrect: Mapped[int] = mapped_column(Integer, default=0)
    
    # Next review date
    next_review_date: Mapped[date] = mapped_column(Date, default=date.today)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Tracking
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="word_progress")
    word: Mapped["Word"] = relationship("Word", back_populates="user_progress")
    
    # Ensure one progress record per user-word combination
    __table_args__ = (
        UniqueConstraint('user_id', 'word_id', name='uq_user_word'),
        Index('idx_user_next_review', 'user_id', 'next_review_date'),
        Index('idx_leitner_box', 'leitner_box'),
    )

    def __repr__(self):
        return f"<UserWordProgress(user_id={self.user_id}, word_id={self.word_id}, box={self.leitner_box})>"


class StudySession(Base):
    """Tracks study sessions for analytics and progress monitoring"""
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # Session details
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Statistics
    words_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    words_correct: Mapped[int] = mapped_column(Integer, default=0)
    words_incorrect: Mapped[int] = mapped_column(Integer, default=0)
    new_words: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="study_sessions")
    
    __table_args__ = (
        Index('idx_user_started', 'user_id', 'started_at'),
    )

    def __repr__(self):
        return f"<StudySession(id={self.id}, user_id={self.user_id}, started={self.started_at})>"


class WordEditHistory(Base):
    """Tracks edits made to words for audit trail"""
    __tablename__ = "word_edit_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id"), nullable=False)
    edited_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # What was changed
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)  # word, definition, example, translation
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tracking
    edited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    word: Mapped["Word"] = relationship("Word", back_populates="edit_history")
    edited_by_user: Mapped["User"] = relationship("User", back_populates="word_edits")
    
    __table_args__ = (
        Index('idx_word_edited', 'word_id', 'edited_at'),
        Index('idx_user_edited', 'edited_by', 'edited_at'),
    )

    def __repr__(self):
        return f"<WordEditHistory(word_id={self.word_id}, field={self.field_name}, edited_by={self.edited_by})>"
