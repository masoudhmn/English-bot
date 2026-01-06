"""
Handlers package for the English Learning Bot.

This package organizes all Telegram bot handlers into logical modules:
- base: Base utilities and decorators
- start: User registration and setup
- learning: Learning session flow
- words: Word management (add, edit)
- settings: User settings
- progress: Statistics and progress tracking
"""

from src.handlers.base import error_handler, get_user_or_error
from src.handlers.start import (
    start_command,
    set_word_limit,
    cancel_command,
)
from src.handlers.learning import (
    start_learning,
    show_next_word,
    handle_answer,
    handle_difficulty,
    handle_next_word,
    end_learning_session,
)
from src.handlers.words import (
    add_words_prompt,
    handle_excel_file,
    send_sample_excel,
    edit_word_prompt,
    select_word_to_edit,
    handle_edit_field_selection,
    handle_edit_value,
)
from src.handlers.settings import (
    show_settings,
    handle_settings_buttons,
    set_reminder_time,
)
from src.handlers.progress import show_progress

# Re-export conversation states for backward compatibility
from src.constants import ConversationState

# Expose states with old names for backward compatibility
WAITING_WORD_LIMIT = ConversationState.WAITING_WORD_LIMIT
WAITING_EXCEL_FILE = ConversationState.WAITING_EXCEL_FILE
WAITING_WORD_TO_EDIT = ConversationState.WAITING_WORD_TO_EDIT
WAITING_EDIT_VALUE = ConversationState.WAITING_EDIT_VALUE
SETTINGS_MENU = ConversationState.SETTINGS_MENU
WAITING_REMINDER_TIME = ConversationState.WAITING_REMINDER_TIME

__all__ = [
    # Base
    "error_handler",
    "get_user_or_error",
    
    # Start
    "start_command",
    "set_word_limit",
    "cancel_command",
    
    # Learning
    "start_learning",
    "show_next_word",
    "handle_answer",
    "handle_difficulty",
    "handle_next_word",
    "end_learning_session",
    
    # Words
    "add_words_prompt",
    "handle_excel_file",
    "send_sample_excel",
    "edit_word_prompt",
    "select_word_to_edit",
    "handle_edit_field_selection",
    "handle_edit_value",
    
    # Settings
    "show_settings",
    "handle_settings_buttons",
    "set_reminder_time",
    
    # Progress
    "show_progress",
    
    # States
    "ConversationState",
    "WAITING_WORD_LIMIT",
    "WAITING_EXCEL_FILE",
    "WAITING_WORD_TO_EDIT",
    "WAITING_EDIT_VALUE",
    "SETTINGS_MENU",
    "WAITING_REMINDER_TIME",
]
