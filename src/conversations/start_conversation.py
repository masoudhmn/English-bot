"""
Start conversation handler for user registration and setup.
"""

from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters

from src.constants import ConversationState
from src.handlers import start_command, set_word_limit, cancel_command
from src.logger import setup_logger

logger = setup_logger(__name__)


def create_start_conversation() -> ConversationHandler:
    """
    Create the /start conversation handler.
    
    This conversation handles:
    - User registration
    - Setting daily word limit
    """
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command)
        ],
        states={
            ConversationState.WAITING_WORD_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_word_limit)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        name="start_conversation",
        persistent=False,
    )
