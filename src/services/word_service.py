"""
Word service - handles word management and editing logic.
"""

from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Word, WordEditHistory
from src.logger import setup_logger

logger = setup_logger(__name__)


async def get_word_by_text(session: AsyncSession, word_text: str) -> Optional[Word]:
    """
    Find a word by text (case-insensitive).
    
    Args:
        session: Database session
        word_text: Word text to search for
        
    Returns:
        Word object if found, None otherwise
    """
    stmt = select(Word).where(Word.word.ilike(word_text))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def edit_word_field(
    session: AsyncSession,
    word_id: int,
    field_name: str,
    new_value: str,
    edited_by: int
) -> Word:
    """
    Edit a specific field of a word.
    
    Args:
        session: Database session
        word_id: ID of the word to edit
        field_name: Name of the field to edit
        new_value: New value for the field
        edited_by: User ID who is editing
        
    Returns:
        Updated Word object
        
    Raises:
        ValueError: If word not found or invalid field name
    """
    # Get word from database
    stmt = select(Word).where(Word.id == word_id)
    result = await session.execute(stmt)
    word = result.scalar_one_or_none()
    
    if not word:
        raise ValueError(f"Word {word_id} not found")
    
    # Validate field name
    valid_fields = ['word', 'definition', 'example', 'translation']
    if field_name not in valid_fields:
        raise ValueError(f"Invalid field name: {field_name}")
    
    # Get old value for history
    old_value = getattr(word, field_name, None)
    
    # Update word
    setattr(word, field_name, new_value)
    word.updated_at = datetime.utcnow()
    
    # Record edit history
    edit_history = WordEditHistory(
        word_id=word_id,
        edited_by=edited_by,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value
    )
    session.add(edit_history)
    await session.commit()
    await session.refresh(word)
    
    logger.info(f"User {edited_by} updated word {word_id} field {field_name}")
    return word


async def create_word_from_excel(
    session: AsyncSession,
    word_text: str,
    definition: str,
    example: Optional[str] = None,
    translation: Optional[str] = None,
    added_by: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Create a word from Excel data.
    
    Args:
        session: Database session
        word_text: Word text
        definition: Word definition
        example: Example sentence (optional)
        translation: Translation (optional)
        added_by: User ID who added the word
        
    Returns:
        Tuple of (success, message)
    """
    # Check for duplicates
    existing = await get_word_by_text(session, word_text)
    if existing:
        return False, f"Word '{word_text}' already exists"
    
    # Create new word
    new_word = Word(
        word=word_text,
        definition=definition,
        example=example,
        translation=translation,
        added_by=added_by
    )
    session.add(new_word)
    await session.commit()
    
    logger.info(f"Created word '{word_text}' by user {added_by}")
    return True, f"Added word '{word_text}'"
