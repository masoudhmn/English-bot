"""
Edit word conversation handler for modifying existing words.
"""

from telegram.ext import MessageHandler, CommandHandler, ConversationHandler, filters

from src.constants import ConversationState, ButtonText
from src.handlers import edit_word_prompt, select_word_to_edit, cancel_command
from src.logger import setup_logger

logger = setup_logger(__name__)


def create_edit_word_conversation() -> ConversationHandler:
    """
    Create Edit Word conversation handler.
    
    This conversation handles:
    - Word selection
    - Field selection
    - Value input
    """
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(f"^{ButtonText.EDIT_WORD}$"),
                edit_word_prompt
            ),
        ],
        states={
            ConversationState.WAITING_WORD_TO_EDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_word_to_edit)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        name="edit_word_conversation",
        persistent=False,
    )
