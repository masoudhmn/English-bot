"""
Settings handlers for English Learning Bot.

This module handles:
- Settings menu display
- Daily word limit configuration
- Reminder toggle and time settings
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.database import get_session
from src.keyboards import get_main_menu_keyboard, get_settings_keyboard
from src.constants import ConversationState, Messages
from src.callback_data import SettingsCallback
from src.services import update_user_settings, toggle_reminder, set_user_reminder_time
from src.handlers.base import get_user_from_db, log_handler
from src.logger import setup_logger

logger = setup_logger(__name__)


@log_handler("show_settings")
async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display settings menu with current user preferences.
    
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
                # Send new message with reply keyboard (can't edit to change keyboard type)
                await query.message.reply_text(
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
                # Toggle reminder using service
                user, enabled = await toggle_reminder(session, user_id)
                
                # Rebuild settings message with updated values
                message = (
                    f"⚙️ Settings\n\n"
                    f"📈 Daily Word Limit: {user.daily_word_limit}\n"
                    f"🔔 Reminder: {'Enabled' if user.reminder_enabled else 'Disabled'}\n"
                    f"⏰ Reminder Time: {user.reminder_time}\n"
                )
                
                # Update message and keyboard (both inline, so edit works)
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
                # Send new message (can't edit inline to reply keyboard)
                await query.message.reply_text(
                    "What would you like to do next?",
                    reply_markup=get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error handling settings button: {e}")
        # Send new message with reply keyboard on error
        await query.message.reply_text(
            Messages.ERROR_GENERIC,
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END


@log_handler("set_reminder_time")
async def set_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle reminder time input from user.
    
    Validates time format (HH:MM) and saves to database.
    
    Returns:
        WAITING_REMINDER_TIME if invalid, END if successful
    """
    if not update.message or not update.message.text:
        return ConversationState.WAITING_REMINDER_TIME
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Save to database using service (which validates time format)
    try:
        async with get_session() as session:
            user = await set_user_reminder_time(session, user_id, text)
                
            await update.message.reply_text(
                Messages.SUCCESS_REMINDER_TIME_SET.format(time=user.reminder_time),
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
                
    except ValueError as e:
        # Time format validation failed
        await update.message.reply_text(
            Messages.ERROR_INVALID_TIME,
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_REMINDER_TIME
    except Exception as e:
        logger.error(f"Error setting reminder time: {e}")
        await update.message.reply_text(
            Messages.ERROR_GENERIC,
            reply_markup=get_main_menu_keyboard()
        )
    
    return ConversationHandler.END
