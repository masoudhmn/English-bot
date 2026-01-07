"""
User service - handles user management and registration logic.
"""

from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.logger import setup_logger

logger = setup_logger(__name__)


async def create_user(
    session: AsyncSession,
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> User:
    """
    Create a new user in the database.
    
    Args:
        session: Database session
        user_id: Telegram user ID
        username: Telegram username (optional)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        
    Returns:
        Created User object
    """
    user = User(
        id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    logger.info(f"Created new user {user_id}")
    return user


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> Tuple[User, bool]:
    """
    Get existing user or create new one.
    
    Args:
        session: Database session
        user_id: Telegram user ID
        username: Telegram username (optional)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        
    Returns:
        Tuple of (User object, is_new boolean)
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = await create_user(session, user_id, username, first_name, last_name)
        return user, True
    
    # Update user info if changed
    needs_update = (
        user.username != username or
        user.first_name != first_name or
        user.last_name != last_name
    )
    
    if needs_update:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.last_active = datetime.utcnow()
        await session.commit()
        logger.info(f"Updated user info for {user_id}")
    
    return user, False


async def update_user_settings(
    session: AsyncSession,
    user_id: int,
    daily_word_limit: Optional[int] = None
) -> User:
    """
    Update user settings.
    
    Args:
        session: Database session
        user_id: Telegram user ID
        daily_word_limit: New daily word limit (optional)
        
    Returns:
        Updated User object
        
    Raises:
        ValueError: If user not found
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    if daily_word_limit is not None:
        user.daily_word_limit = daily_word_limit
    
    await session.commit()
    await session.refresh(user)
    
    logger.info(f"Updated settings for user {user_id}")
    return user


async def toggle_reminder(
    session: AsyncSession,
    user_id: int
) -> Tuple[User, bool]:
    """
    Toggle reminder on/off for a user.
    
    Args:
        session: Database session
        user_id: Telegram user ID
        
    Returns:
        Tuple of (User object, new_enabled_state)
        
    Raises:
        ValueError: If user not found
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    user.reminder_enabled = not user.reminder_enabled
    await session.commit()
    await session.refresh(user)
    
    logger.info(f"Toggled reminder for user {user_id} to {user.reminder_enabled}")
    return user, user.reminder_enabled


async def set_reminder_time(
    session: AsyncSession,
    user_id: int,
    time_str: str
) -> User:
    """
    Set reminder time for a user.
    
    Args:
        session: Database session
        user_id: Telegram user ID
        time_str: Time in HH:MM format
        
    Returns:
        Updated User object
        
    Raises:
        ValueError: If user not found or time format invalid
    """
    # Validate time format
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        raise ValueError(f"Invalid time format: {time_str}")
    
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    user.reminder_time = time_str
    await session.commit()
    await session.refresh(user)
    
    logger.info(f"Set reminder time for user {user_id} to {time_str}")
    return user
