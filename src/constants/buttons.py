"""
Button text constants for Telegram keyboards.
"""

from enum import Enum


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
