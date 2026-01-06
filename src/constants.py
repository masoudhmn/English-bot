"""
Constants module for the English Learning Bot.

This module centralizes all constants used throughout the application,
including conversation states, callback data patterns, session keys, and UI text.
"""

from enum import Enum, IntEnum, auto


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


class CallbackPrefix(str, Enum):
    """
    Callback data prefixes for inline buttons.
    Using consistent prefixes makes routing and parsing easier.
    """
    # Answer buttons
    ANSWER = "answer"
    
    # Difficulty buttons
    DIFFICULTY = "difficulty"
    
    # Learning flow
    NEXT_WORD = "next_word"
    STOP_LEARNING = "stop_learning"
    START_LEARNING = "start_learning"
    
    # Edit word
    EDIT_FIELD = "edit_field"
    EDIT_CANCEL = "edit_cancel"
    
    # Settings
    SETTINGS = "settings"
    
    # Confirmation
    CONFIRM = "confirm"


class CallbackAction(str, Enum):
    """
    Specific callback actions for buttons.
    """
    # Answer actions
    ANSWER_CORRECT = "answer:correct"
    ANSWER_INCORRECT = "answer:incorrect"
    
    # Next/Stop actions
    NEXT_WORD = "next:word"
    STOP_LEARNING = "next:stop"
    START_LEARNING_NOW = "start:now"
    START_LEARNING_LATER = "start:later"
    
    # Edit field actions
    EDIT_WORD = "edit:word"
    EDIT_DEFINITION = "edit:definition"
    EDIT_EXAMPLE = "edit:example"
    EDIT_TRANSLATION = "edit:translation"
    EDIT_CANCEL = "edit:cancel"
    
    # Settings actions
    SETTINGS_LIMIT = "settings:limit"
    SETTINGS_REMINDER = "settings:reminder"
    SETTINGS_TIME = "settings:time"
    SETTINGS_BACK = "settings:back"
    
    # Confirmation actions
    CONFIRM_YES = "confirm:yes"
    CONFIRM_NO = "confirm:no"


class Difficulty(str, Enum):
    """Difficulty levels for word review."""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class ButtonText:
    """
    UI button text constants.
    Centralized for easy localization and consistency.
    """
    # Main menu buttons
    START_LEARNING = "📚 Start Learning"
    MY_PROGRESS = "📊 My Progress"
    ADD_WORDS = "➕ Add Words"
    EDIT_WORD = "✏️ Edit Word"
    SETTINGS = "⚙️ Settings"
    SAMPLE_EXCEL = "📖 Sample Excel"
    
    # Answer buttons
    I_KNOW = "✅ I Know"
    I_DONT_KNOW = "❌ I Don't Know"
    
    # Difficulty buttons
    EASY = "😊 Easy"
    NORMAL = "😐 Normal"
    HARD = "😓 Hard"
    
    # Navigation buttons
    NEXT_WORD = "➡️ Next Word"
    STOP_LEARNING = "🛑 Stop Learning"
    START_NOW = "🚀 Start Now"
    LATER = "⏰ Later"
    
    # Edit buttons
    WORD = "📝 Word"
    DEFINITION = "📖 Definition"
    EXAMPLE = "💬 Example"
    TRANSLATION = "🌐 Translation"
    CANCEL = "❌ Cancel"
    
    # Settings buttons
    SET_DAILY_LIMIT = "📈 Set Daily Word Limit"
    ENABLE_REMINDER = "🔔 Enable Reminder"
    DISABLE_REMINDER = "🔕 Disable Reminder"
    SET_REMINDER_TIME = "⏰ Set Reminder Time"
    BACK = "🔙 Back"
    
    # Confirmation
    YES = "✅ Yes"
    NO = "❌ No"


class Messages:
    """
    Bot message templates.
    Centralized for consistency and easy modification.
    """
    # Errors
    ERROR_GENERIC = "❌ An error occurred. Please try again later."
    ERROR_USER_NOT_FOUND = "❌ User not found. Please use /start first."
    ERROR_WORD_NOT_FOUND = "❌ Word not found."
    ERROR_SESSION_EXPIRED = "❌ Session expired. Please start again."
    ERROR_INVALID_NUMBER = "❌ Please enter a valid number."
    ERROR_NUMBER_RANGE = "❌ Please enter a number between {min} and {max}."
    ERROR_INVALID_TIME = "❌ Invalid format. Please enter time in 24-hour format (HH:MM)."
    
    # Success
    SUCCESS_OPERATION_CANCELLED = "✅ Operation cancelled."
    SUCCESS_WORD_LIMIT_SET = "✅ Great! You'll practice {limit} words per day.\n\nUse the menu below to get started!"
    SUCCESS_WORDS_ADDED = "✅ Successfully added {count} words!"
    SUCCESS_WORD_UPDATED = "✅ Updated **{word}**\n\n{field}: {value}"
    SUCCESS_REMINDER_TIME_SET = "✅ Reminder time updated to **{time}**!"
    
    # Prompts
    PROMPT_USE_MENU = "I didn't understand that. Please use the menu buttons below."
    PROMPT_WORD_LIMIT = "How many words would you like to practice each day?"
    PROMPT_UPLOAD_EXCEL = (
        "📤 Upload Excel File\n\n"
        "Send me an Excel file (.xlsx) with your words.\n\n"
        "Required columns:\n"
        "• word\n"
        "• definition\n\n"
        "Optional columns:\n"
        "• example\n"
        "• translation\n\n"
        "Use /sample to get a sample Excel template."
    )
    PROMPT_EDIT_WORD = "✏️ Edit Word\n\nEnter the word you want to edit:"
    PROMPT_EDIT_VALUE = "✏️ Enter new value for **{field}**:"
    PROMPT_REMINDER_TIME = "⏰ Enter new reminder time in HH:MM format (24-hour):"
    
    # Learning
    NO_WORDS_TO_REVIEW = (
        "🎉 Great job! You have no words to review today.\n"
        "Add more words or come back tomorrow!"
    )
    SESSION_STARTING = (
        "📚 Starting learning session!\n"
        "📊 Review: {review_count} words\n"
        "✨ New: {new_count} words\n"
        "📈 Total: {total_count} words\n\n"
        "Let's begin! 🚀"
    )
    
    @staticmethod
    def welcome_new_user(first_name: str) -> str:
        return (
            f"👋 Welcome {first_name}!\n\n"
            "🎯 I'm your English Learning Bot using the Leitner study method!\n\n"
            "📝 First, let's set your daily word limit.\n"
            "How many words would you like to practice each day?"
        )
    
    @staticmethod
    def welcome_back(first_name: str) -> str:
        return (
            f"👋 Welcome back, {first_name}!\n\n"
            "Choose an option from the menu below:"
        )
