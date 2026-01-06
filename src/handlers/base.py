"""
Base handler utilities for the English Learning Bot.

This module provides common utilities, decorators, and error handling
used across all handler modules.
"""

from functools import wraps
from typing import Optional, Callable, Any, TypeVar, Tuple
import traceback

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import TelegramError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models import User
from src.keyboards import get_main_menu_keyboard
from src.constants import Messages, SessionKey
from src.logger import setup_logger

logger = setup_logger(__name__)

# Type variable for handler functions
F = TypeVar('F', bound=Callable[..., Any])


async def get_user_from_db(session: AsyncSession, user_id: int) -> Optional[User]:
    """
    Retrieve a user from the database by their Telegram ID.
    
    Args:
        session: Database session
        user_id: Telegram user ID
        
    Returns:
        User object if found, None otherwise
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_or_error(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession
) -> Tuple[Optional[User], bool]:
    """
    Get user from database or send error message.
    
    Args:
        update: Telegram update
        context: Bot context
        session: Database session
        
    Returns:
        Tuple of (User or None, success boolean)
    """
    user_id = update.effective_user.id
    user = await get_user_from_db(session, user_id)
    
    if not user:
        message = Messages.ERROR_USER_NOT_FOUND
        if update.callback_query:
            await update.callback_query.answer(message, show_alert=True)
        elif update.message:
            await update.message.reply_text(message, reply_markup=get_main_menu_keyboard())
        return None, False
    
    return user, True


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler for the bot.
    
    Logs the error and sends a user-friendly message.
    
    Args:
        update: The update that caused the error
        context: Bot context containing the error
    """
    # Log the error
    logger.error(
        f"Exception while handling an update: {context.error}",
        exc_info=context.error
    )
    
    # Log the full traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    logger.error(f"Traceback:\n{tb_string}")
    
    # Send error message to user if possible
    if isinstance(update, Update):
        error_message = Messages.ERROR_GENERIC
        
        try:
            if update.callback_query:
                await update.callback_query.answer(error_message, show_alert=True)
            elif update.message:
                await update.message.reply_text(
                    error_message,
                    reply_markup=get_main_menu_keyboard()
                )
        except TelegramError as e:
            logger.error(f"Failed to send error message to user: {e}")


def clear_session_data(context: ContextTypes.DEFAULT_TYPE, keys: list = None) -> None:
    """
    Clear session data from context.
    
    Args:
        context: Bot context
        keys: Specific keys to clear. If None, clears all user_data.
    """
    if keys is None:
        context.user_data.clear()
    else:
        for key in keys:
            context.user_data.pop(key, None)


def get_session_value(context: ContextTypes.DEFAULT_TYPE, key: SessionKey, default=None):
    """
    Safely get a value from session data.
    
    Args:
        context: Bot context
        key: Session key (from SessionKey enum)
        default: Default value if key not found
        
    Returns:
        The stored value or default
    """
    return context.user_data.get(key.value if isinstance(key, SessionKey) else key, default)


def set_session_value(context: ContextTypes.DEFAULT_TYPE, key: SessionKey, value) -> None:
    """
    Safely set a value in session data.
    
    Args:
        context: Bot context
        key: Session key (from SessionKey enum)
        value: Value to store
    """
    context.user_data[key.value if isinstance(key, SessionKey) else key] = value


async def send_message(
    update: Update,
    text: str,
    reply_markup=None,
    parse_mode: str = "Markdown",
    edit: bool = False
) -> None:
    """
    Send or edit a message based on the update type.
    
    Args:
        update: Telegram update
        text: Message text
        reply_markup: Optional keyboard markup
        parse_mode: Message parse mode
        edit: Whether to edit the existing message (for callback queries)
    """
    try:
        if update.callback_query and edit:
            await update.callback_query.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        elif update.message:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    except TelegramError as e:
        logger.error(f"Failed to send message: {e}")
        # Try without parse mode if formatting failed
        if "parse" in str(e).lower():
            await send_message(update, text, reply_markup, parse_mode=None, edit=edit)


def log_handler(func_name: str):
    """
    Decorator to log handler entry and exit.
    
    Args:
        func_name: Name of the handler for logging
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else "unknown"
            logger.debug(f"Handler {func_name} called by user {user_id}")
            
            try:
                result = await func(update, context, *args, **kwargs)
                logger.debug(f"Handler {func_name} completed for user {user_id}")
                return result
            except Exception as e:
                logger.error(f"Handler {func_name} failed for user {user_id}: {e}")
                raise
        
        return wrapper
    return decorator
