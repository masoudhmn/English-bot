"""
Add words conversation handler for Excel file upload.
"""

from telegram.ext import MessageHandler, CommandHandler, ConversationHandler, filters

from src.constants import ConversationState, ButtonText
from src.handlers import add_words_prompt, handle_excel_file, cancel_command
from src.logger import setup_logger

logger = setup_logger(__name__)


def create_add_words_conversation() -> ConversationHandler:
    """
    Create Add Words conversation handler.
    
    This conversation handles:
    - Excel file upload
    - Word validation and import
    """
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(f"^{ButtonText.ADD_WORDS}$"),
                add_words_prompt
            ),
        ],
        states={
            ConversationState.WAITING_EXCEL_FILE: [
                MessageHandler(
                    filters.Document.FileExtension("xlsx"),
                    handle_excel_file
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        name="add_words_conversation",
        persistent=False,
    )
