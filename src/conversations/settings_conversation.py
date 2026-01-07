"""
Settings conversation handler for user preferences.
"""

from telegram.ext import MessageHandler, CommandHandler, ConversationHandler, CallbackQueryHandler, filters

from src.constants import ConversationState, ButtonText
from src.handlers import show_settings, handle_settings_buttons, set_word_limit, set_reminder_time, cancel_command
from src.callback_data import SettingsCallback
from src.logger import setup_logger

logger = setup_logger(__name__)


def create_settings_conversation() -> ConversationHandler:
    """
    Create Settings conversation handler.
    
    This conversation handles:
    - Settings menu display
    - Daily word limit
    - Reminder toggle
    - Reminder time setting
    """
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(f"^{ButtonText.SETTINGS}$"),
                show_settings
            )
        ],
        states={
            ConversationState.SETTINGS_MENU: [
                CallbackQueryHandler(
                    handle_settings_buttons,
                    pattern=SettingsCallback.pattern()
                )
            ],
            ConversationState.WAITING_WORD_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_word_limit)
            ],
            ConversationState.WAITING_REMINDER_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_time)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(
                handle_settings_buttons,
                pattern=r"^settings:back$"
            )
        ],
        name="settings_conversation",
        persistent=False,
    )
