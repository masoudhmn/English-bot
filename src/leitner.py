"""Leitner Study Method Implementation"""

from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import UserWordProgress, Word, User
from src.config import LEITNER_BOXES


async def get_words_for_review(
    session: AsyncSession, 
    user_id: int, 
    limit: int = 10
) -> List[UserWordProgress]:
    """
    Get words that need to be reviewed based on Leitner system.
    
    Returns words that:
    1. Are due for review (next_review_date <= today)
    2. Haven't been seen yet
    
    Prioritizes words in lower Leitner boxes (need more practice).
    """
    today = date.today()
    
    # Get words due for review, ordered by box (lower boxes first)
    stmt = (
        select(UserWordProgress)
        .where(
            and_(
                UserWordProgress.user_id == user_id,
                UserWordProgress.next_review_date <= today
            )
        )
        .order_by(UserWordProgress.leitner_box.asc())
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    words_to_review = list(result.scalars().all())
    
    return words_to_review


async def get_new_words(
    session: AsyncSession, 
    user_id: int, 
    limit: int = 5
) -> List[Word]:
    """
    Get new words that the user hasn't seen yet.
    """
    # Get all word IDs the user has already seen
    stmt_seen = select(UserWordProgress.word_id).where(
        UserWordProgress.user_id == user_id
    )
    result_seen = await session.execute(stmt_seen)
    seen_word_ids = set(result_seen.scalars().all())
    
    # Get words not yet seen
    stmt_new = (
        select(Word)
        .where(
            and_(
                Word.is_active == True,
                Word.id.notin_(seen_word_ids) if seen_word_ids else True
            )
        )
        .limit(limit)
    )
    
    result_new = await session.execute(stmt_new)
    new_words = list(result_new.scalars().all())
    
    return new_words


async def update_word_progress(
    session: AsyncSession,
    user_id: int,
    word_id: int,
    is_correct: bool,
    difficulty: Optional[str] = None
) -> UserWordProgress:
    """
    Update user's progress with a word based on their response.
    
    Leitner Logic:
    - If correct: Move to next box (increase review interval)
    - If incorrect: Move back to box 1 (review tomorrow)
    - Difficulty affects the scheduling slightly
    """
    # Get or create progress record
    stmt = select(UserWordProgress).where(
        and_(
            UserWordProgress.user_id == user_id,
            UserWordProgress.word_id == word_id
        )
    )
    result = await session.execute(stmt)
    progress = result.scalar_one_or_none()
    
    if not progress:
        # Create new progress record
        progress = UserWordProgress(
            user_id=user_id,
            word_id=word_id,
            leitner_box=1,
            next_review_date=date.today() + timedelta(days=1)
        )
        session.add(progress)
    
    # Update statistics
    progress.times_reviewed += 1
    if is_correct:
        progress.times_correct += 1
    else:
        progress.times_incorrect += 1
    
    # Update difficulty if provided
    if difficulty:
        progress.difficulty = difficulty
    
    # Update Leitner box and next review date
    if is_correct:
        # Move to next box (max box 7)
        new_box = min(progress.leitner_box + 1, 7)
        progress.leitner_box = new_box
        
        # Calculate next review date based on new box
        days_until_review = LEITNER_BOXES[new_box]
        
        # Adjust based on difficulty
        if difficulty == "easy" and new_box < 7:
            # If it's easy, review even less frequently
            days_until_review = int(days_until_review * 1.5)
        elif difficulty == "hard":
            # If it's hard, review more frequently
            days_until_review = max(1, int(days_until_review * 0.7))
        
        progress.next_review_date = date.today() + timedelta(days=days_until_review)
    else:
        # Move back to box 1 (needs more practice)
        progress.leitner_box = 1
        progress.next_review_date = date.today() + timedelta(days=1)
    
    progress.last_reviewed_at = progress.updated_at
    
    await session.commit()
    await session.refresh(progress)
    
    return progress


async def get_user_statistics(session: AsyncSession, user_id: int) -> dict:
    """
    Get user's learning statistics.
    """
    stmt = select(UserWordProgress).where(UserWordProgress.user_id == user_id)
    result = await session.execute(stmt)
    all_progress = list(result.scalars().all())
    
    total_words = len(all_progress)
    
    # Count words in each box
    box_counts = {}
    for i in range(1, 8):
        box_counts[i] = sum(1 for p in all_progress if p.leitner_box == i)
    
    # Words mastered (box 7)
    mastered = box_counts.get(7, 0)
    
    # Total reviews
    total_reviews = sum(p.times_reviewed for p in all_progress)
    total_correct = sum(p.times_correct for p in all_progress)
    total_incorrect = sum(p.times_incorrect for p in all_progress)
    
    # Accuracy
    accuracy = (total_correct / total_reviews * 100) if total_reviews > 0 else 0
    
    # Words due for review today
    today = date.today()
    due_today = sum(1 for p in all_progress if p.next_review_date <= today)
    
    return {
        "total_words": total_words,
        "mastered_words": mastered,
        "box_distribution": box_counts,
        "total_reviews": total_reviews,
        "total_correct": total_correct,
        "total_incorrect": total_incorrect,
        "accuracy": round(accuracy, 2),
        "due_today": due_today,
    }
