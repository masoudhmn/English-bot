"""
Start and user setup handlers for the English Learning Bot.

This module handles:
- /start command and user registration
- Word limit configuration
- Cancel operation
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.database import get_session
from src.keyboards import get_main_menu_keyboard
from src.constants import ConversationState, Messages
from src.services import get_or_create_user, update_user_settings
from src.handlers.base import log_handler
from src.logger import setup_logger

logger = setup_logger(__name__)


@log_handler("start_command")
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    
    Creates new user or welcomes back existing user.
    New users are prompted to set their daily word limit.
    
    Returns:
        WAITING_WORD_LIMIT for new users, END for existing users
    """
    user = update.effective_user
    if not user:
        return ConversationHandler.END
    
    logger.info(f"User {user.id} started the bot")
    
    try:
        async with get_session() as session:
            # Get or create user using service
            db_user, is_new = await get_or_create_user(
                session, user.id, user.username, user.first_name, user.last_name
            )
            
            if is_new:
                # Welcome new user and ask for word limit
                welcome_message = Messages.welcome_new_user(user.first_name or "there")
                await update.message.reply_text(welcome_message)
                return ConversationState.WAITING_WORD_LIMIT
        
        # Welcome back existing user
        welcome_back = Messages.welcome_back(user.first_name or "there")
        await update.message.reply_text(
            welcome_back,
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(Messages.ERROR_GENERIC)
        return ConversationHandler.END


@log_handler("set_word_limit")
async def set_word_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle word limit input from user.
    
    Validates the input (1-100) and saves to database.
    
    Returns:
        WAITING_WORD_LIMIT if invalid, END if successful
    """
    if not update.message or not update.message.text:
        return ConversationState.WAITING_WORD_LIMIT
    
    try:
        limit = int(update.message.text.strip())
        
        # Validate range
        if limit < 1 or limit > 100:
            await update.message.reply_text(
                Messages.ERROR_NUMBER_RANGE.format(min=1, max=100)
            )
            return ConversationState.WAITING_WORD_LIMIT
        
        # Save to database using service
        user_id = update.effective_user.id
        async with get_session() as session:
            await update_user_settings(session, user_id, daily_word_limit=limit)
            logger.info(f"User {user_id} set daily limit to {limit}")
        
        # Send success message
        await update.message.reply_text(
            Messages.SUCCESS_WORD_LIMIT_SET.format(limit=limit),
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(Messages.ERROR_INVALID_NUMBER)
        return ConversationState.WAITING_WORD_LIMIT
        
    except Exception as e:
        logger.error(f"Error in set_word_limit: {e}")
        await update.message.reply_text(Messages.ERROR_GENERIC)
        return ConversationHandler.END


@log_handler("cancel_command")
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /cancel command.
    
    Clears user session data and returns to main menu.
    
    Returns:
        END to terminate any conversation
    """
    # Clear session data
    if context.user_data:
        context.user_data.clear()
    
    await update.message.reply_text(
        Messages.SUCCESS_OPERATION_CANCELLED,
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END
