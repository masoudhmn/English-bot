"""Leitner Study Method Implementation"""

from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import UserWordProgress, Word, DifficultyLevel
from src.config import LEITNER_BOXES
from src.logger import setup_logger

logger = setup_logger(__name__)

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
    
    try:
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
        
        logger.info(f"Retrieved {len(words_to_review)} words for review for user {user_id}")
        return words_to_review
        
    except Exception as e:
        logger.error(f"Error getting words for review: {e}")
        return []


async def get_new_words(
    session: AsyncSession, 
    user_id: int, 
    limit: int = 5
) -> List[Word]:
    """
    Get new words that the user hasn't seen yet.
    """
    try:
        # Optimized query using LEFT JOIN to find words with no progress record for this user
        stmt = (
            select(Word)
            .outerjoin(
                UserWordProgress, 
                and_(
                    Word.id == UserWordProgress.word_id, 
                    UserWordProgress.user_id == user_id
                )
            )
            .where(
                and_(
                    Word.is_active == True,
                    UserWordProgress.id.is_(None)  # No progress record found
                )
            )
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        new_words = list(result.scalars().all())
        
        logger.info(f"Retrieved {len(new_words)} new words for user {user_id}")
        return new_words
        
    except Exception as e:
        logger.error(f"Error getting new words: {e}")
        return []


async def update_word_progress(
    session: AsyncSession,
    user_id: int,
    word_id: int,
    is_correct: bool,
    difficulty: Optional[str] = None
) -> Optional[UserWordProgress]:
    """
    Update user's progress with a word based on their response.
    
    Leitner Logic:
    - If correct: Move to next box (increase review interval)
    - If incorrect: Move back to box 1 (review tomorrow)
    - Difficulty affects the scheduling slightly
    """
    try:
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
                next_review_date=date.today() + timedelta(days=1),
                times_reviewed=0,
                times_correct=0,
                times_incorrect=0
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
            days_until_review = LEITNER_BOXES.get(new_box, 1)
            
            # Adjust based on difficulty
            if difficulty == DifficultyLevel.EASY and new_box < 7:
                # If it's easy, review even less frequently
                days_until_review = int(days_until_review * 1.5)
            elif difficulty == DifficultyLevel.HARD:
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
        
    except Exception as e:
        logger.error(f"Error updating word progress: {e}")
        await session.rollback()
        raise


async def get_user_statistics(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    """
    Get user's learning statistics.
    """
    try:
        stmt = select(UserWordProgress).where(UserWordProgress.user_id == user_id)
        result = await session.execute(stmt)
        all_progress = list(result.scalars().all())
        
        total_words = len(all_progress)
        
        # Count words in each box
        box_counts = {i: 0 for i in range(1, 8)}
        for p in all_progress:
            if p.leitner_box in box_counts:
                box_counts[p.leitner_box] += 1
        
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
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {
            "total_words": 0,
            "mastered_words": 0,
            "box_distribution": {},
            "total_reviews": 0,
            "total_correct": 0,
            "total_incorrect": 0,
            "accuracy": 0,
            "due_today": 0,
        }
