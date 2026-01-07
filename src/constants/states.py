"""
Conversation states and session keys for the English Learning Bot.
"""

from enum import IntEnum, Enum, auto


class ConversationState(IntEnum):
    """
    Conversation states for ConversationHandler.
    Using IntEnum ensures unique values and compatibility with python-telegram-bot.
    """
    # Initial setup
    WAITING_WORD_LIMIT = auto()
    
    # Add words flow
    WAITING_EXCEL_FILE = auto()
    
    # Edit word flow
    WAITING_WORD_TO_EDIT = auto()
    WAITING_EDIT_VALUE = auto()
    
    # Settings flow
    SETTINGS_MENU = auto()
    WAITING_REMINDER_TIME = auto()


class SessionKey(str, Enum):
    """
    Keys for user_data/context.user_data storage.
    Using str Enum allows direct use as dictionary keys.
    """
    # Learning session
    CURRENT_WORD = "current_word"
    STUDY_SESSION_ID = "study_session_id"
    WORDS_TO_REVIEW = "words_to_review"
    NEW_WORDS = "new_words"
    WORD_INDEX = "word_index"
    LAST_ANSWER_CORRECT = "last_answer_correct"
    
    # Edit session
    EDIT_WORD_ID = "edit_word_id"
    EDIT_FIELD = "edit_field"
