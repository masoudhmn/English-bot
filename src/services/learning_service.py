"""
Learning service - handles learning session management.
"""

from datetime import datetime
from typing import Tuple, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import StudySession, Word
from src.leitner import get_words_for_review, get_new_words, update_word_progress
from src.logger import setup_logger

logger = setup_logger(__name__)


async def create_study_session(
    session: AsyncSession,
    user_id: int,
    daily_limit: int
) -> Tuple[int, List[int], List[int]]:
    """
    Create a new study session and return session data.
    
    Args:
        session: Database session
        user_id: User ID
        daily_limit: Daily word limit
        
    Returns:
        Tuple of (session_id, review_word_ids, new_word_ids)
    """
    # Get words for review
    review_progress = await get_words_for_review(session, user_id, daily_limit)
    review_word_ids = [p.word_id for p in review_progress]
    
    # Get new words
    remaining_slots = daily_limit - len(review_word_ids)
    new_words = []
    if remaining_slots > 0:
        new_words = await get_new_words(session, user_id, remaining_slots)
    new_word_ids = [w.id for w in new_words]
    
    # Create study session record
    study_session = StudySession(user_id=user_id)
    session.add(study_session)
    await session.commit()
    await session.refresh(study_session)
    
    logger.info(
        f"Created session {study_session.id} for user {user_id}: "
        f"{len(review_word_ids)} review, {len(new_word_ids)} new"
    )
    
    return study_session.id, review_word_ids, new_word_ids


async def record_review(
    session: AsyncSession,
    session_id: int,
    word_id: int,
    user_id: int,
    is_correct: bool,
    difficulty: str,
    is_new_word: bool
) -> None:
    """
    Record a word review and update session statistics.
    
    Args:
        session: Database session
        session_id: Study session ID
        word_id: Word ID being reviewed
        user_id: User ID
        is_correct: Whether user answered correctly
        difficulty: Difficulty rating
        is_new_word: Whether this is a new word
    """
    # Update word progress using Leitner system
    await update_word_progress(session, user_id, word_id, is_correct, difficulty)
    
    # Update study session statistics
    stmt = select(StudySession).where(StudySession.id == session_id)
    result = await session.execute(stmt)
    study_session = result.scalar_one_or_none()
    
    if study_session:
        study_session.words_reviewed += 1
        if is_correct:
            study_session.words_correct += 1
        else:
            study_session.words_incorrect += 1
        
        if is_new_word:
            study_session.new_words += 1
        
        await session.commit()


async def end_session(
    session: AsyncSession,
    session_id: int
) -> dict:
    """
    End a study session and return statistics.
    
    Args:
        session: Database session
        session_id: Study session ID
        
    Returns:
        Dictionary with session statistics
    """
    stmt = select(StudySession).where(StudySession.id == session_id)
    result = await session.execute(stmt)
    study_session = result.scalar_one_or_none()
    
    if study_session:
        study_session.ended_at = datetime.utcnow()
        await session.commit()
        
        # Calculate accuracy
        accuracy = 0.0
        if study_session.words_reviewed > 0:
            accuracy = (study_session.words_correct / study_session.words_reviewed) * 100
        
        return {
            "words_reviewed": study_session.words_reviewed,
            "words_correct": study_session.words_correct,
            "words_incorrect": study_session.words_incorrect,
            "new_words": study_session.new_words,
            "accuracy": accuracy,
        }
    
    return {}
