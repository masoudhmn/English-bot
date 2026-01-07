"""
User-facing message templates for the English Learning Bot.
"""

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
