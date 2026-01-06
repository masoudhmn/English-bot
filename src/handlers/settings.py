"""
Settings handlers for the English Learning Bot.

This module handles:
- Settings menu display
- Daily word limit configuration
- Reminder toggle and time settings
"""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.database import get_session
from src.keyboards import get_main_menu_keyboard, get_settings_keyboard
from src.constants import ConversationState, Messages
from src.callback_data import SettingsCallback
from src.handlers.base import get_user_from_db, log_handler
from src.logger import setup_logger

logger = setup_logger(__name__)


@log_handler("show_settings")
async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the settings menu with current user preferences.
    
    Returns:
        SETTINGS_MENU state to handle button selections
    """
    user_id = update.effective_user.id
    
    try:
        async with get_session() as session:
            user = await get_user_from_db(session, user_id)
            
            if not user:
                await update.message.reply_text(Messages.ERROR_USER_NOT_FOUND)
                return ConversationHandler.END
            
            # Build settings message
            message = (
                f"⚙️ Settings\n\n"
                f"📈 Daily Word Limit: {user.daily_word_limit}\n"
                f"🔔 Reminder: {'Enabled' if user.reminder_enabled else 'Disabled'}\n"
                f"⏰ Reminder Time: {user.reminder_time}\n"
            )
            
            await update.message.reply_text(
                message,
                reply_markup=get_settings_keyboard(user.reminder_enabled)
            )
            return ConversationState.SETTINGS_MENU
            
    except Exception as e:
        logger.error(f"Error showing settings: {e}")
        await update.message.reply_text(Messages.ERROR_GENERIC)
        return ConversationHandler.END


@log_handler("handle_settings_buttons")
async def handle_settings_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle settings menu button presses.
    
    Routes to appropriate action based on callback data:
    - settings:limit -> Prompt for new word limit
    - settings:reminder -> Toggle reminder on/off
    - settings:time -> Prompt for new reminder time
    - settings:back -> Return to main menu
    
    Returns:
        Appropriate state for next action
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Parse callback data
    callback = SettingsCallback.decode(query.data)
    if not callback:
        logger.error(f"Failed to parse settings callback: {query.data}")
        return ConversationHandler.END
    
    try:
        async with get_session() as session:
            user = await get_user_from_db(session, user_id)
            
            if not user:
                await query.message.edit_text(
                    Messages.ERROR_USER_NOT_FOUND,
                    reply_markup=get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            # Handle: Set Word Limit
            if callback.is_limit:
                await query.message.edit_text(
                    "📈 *Set Daily Word Limit*\n\n"
                    "Please type a number between 1 and 100:",
                    parse_mode="Markdown"
                )
                return ConversationState.WAITING_WORD_LIMIT
            
            # Handle: Toggle Reminder
            elif callback.is_reminder:
                # Toggle the reminder setting
                user.reminder_enabled = not user.reminder_enabled
                await session.commit()
                
                # Rebuild settings message with updated values
                message = (
                    f"⚙️ Settings\n\n"
                    f"📈 Daily Word Limit: {user.daily_word_limit}\n"
                    f"🔔 Reminder: {'Enabled' if user.reminder_enabled else 'Disabled'}\n"
                    f"⏰ Reminder Time: {user.reminder_time}\n"
                )
                
                # Update message and keyboard
                await query.message.edit_text(
                    message,
                    reply_markup=get_settings_keyboard(user.reminder_enabled)
                )
                
                # Stay in settings menu
                return ConversationState.SETTINGS_MENU
            
            # Handle: Set Reminder Time
            elif callback.is_time:
                await query.message.edit_text(Messages.PROMPT_REMINDER_TIME)
                return ConversationState.WAITING_REMINDER_TIME
            
            # Handle: Back to Main Menu
            elif callback.is_back:
                await query.message.edit_text(
                    "What would you like to do next?",
                    reply_markup=get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error handling settings button: {e}")
        await query.message.edit_text(
            Messages.ERROR_GENERIC,
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END


@log_handler("set_reminder_time")
async def set_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle reminder time input from user.
    
    Validates the time format (HH:MM) and saves to database.
    
    Returns:
        WAITING_REMINDER_TIME if invalid, END if successful
    """
    if not update.message or not update.message.text:
        return ConversationState.WAITING_REMINDER_TIME
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Validate time format
    try:
        valid_time = datetime.strptime(text, "%H:%M").time()
        formatted_time = valid_time.strftime("%H:%M")
    except ValueError:
        await update.message.reply_text(
            Messages.ERROR_INVALID_TIME,
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_REMINDER_TIME
    
    # Save to database
    try:
        async with get_session() as session:
            user = await get_user_from_db(session, user_id)
            
            if user:
                user.reminder_time = formatted_time
                await session.commit()
                
                await update.message.reply_text(
                    Messages.SUCCESS_REMINDER_TIME_SET.format(time=formatted_time),
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await update.message.reply_text(
                    Messages.ERROR_USER_NOT_FOUND,
                    reply_markup=get_main_menu_keyboard()
                )
                
    except Exception as e:
        logger.error(f"Error setting reminder time: {e}")
        await update.message.reply_text(
            Messages.ERROR_GENERIC,
            reply_markup=get_main_menu_keyboard()
        )
    
    return ConversationHandler.END
