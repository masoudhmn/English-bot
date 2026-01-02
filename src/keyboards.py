"""Telegram keyboard layouts for bot UI"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [KeyboardButton("📚 Start Learning"), KeyboardButton("📊 My Progress")],
        [KeyboardButton("➕ Add Words"), KeyboardButton("✏️ Edit Word")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("📖 Sample Excel")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_answer_keyboard():
    """Keyboard for answering if user knows the word"""
    keyboard = [
        [
            InlineKeyboardButton("✅ I Know", callback_data="answer_correct"),
            InlineKeyboardButton("❌ I Don't Know", callback_data="answer_incorrect")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_difficulty_keyboard(word_id: int, is_correct: bool):
    """Keyboard for rating word difficulty"""
    # Encode word_id and is_correct in callback data
    correct_flag = "1" if is_correct else "0"
    keyboard = [
        [
            InlineKeyboardButton("😊 Easy", callback_data=f"difficulty_easy_{word_id}_{correct_flag}"),
            InlineKeyboardButton("😐 Normal", callback_data=f"difficulty_normal_{word_id}_{correct_flag}"),
            InlineKeyboardButton("😓 Hard", callback_data=f"difficulty_hard_{word_id}_{correct_flag}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_continue_keyboard():
    """Keyboard for continuing to next word"""
    keyboard = [
        [
            InlineKeyboardButton("➡️ Next Word", callback_data="next_word"),
            InlineKeyboardButton("🛑 Stop Learning", callback_data="stop_learning")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_field_keyboard():
    """Keyboard for selecting field to edit"""
    keyboard = [
        [
            InlineKeyboardButton("📝 Word", callback_data="edit_field_word"),
            InlineKeyboardButton("📖 Definition", callback_data="edit_field_definition")
        ],
        [
            InlineKeyboardButton("💬 Example", callback_data="edit_field_example"),
            InlineKeyboardButton("🌐 Translation", callback_data="edit_field_translation")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="edit_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard(reminder_enabled: bool):
    """Keyboard for settings"""
    reminder_text = "🔕 Disable Reminder" if reminder_enabled else "🔔 Enable Reminder"
    keyboard = [
        [InlineKeyboardButton("📈 Set Daily Word Limit", callback_data="settings_limit")],
        [InlineKeyboardButton(reminder_text, callback_data="settings_reminder")],
        [InlineKeyboardButton("⏰ Set Reminder Time", callback_data="settings_time")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard():
    """Yes/No confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ No", callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_start_learning_keyboard():
    """Keyboard for starting learning session"""
    keyboard = [
        [
            InlineKeyboardButton("🚀 Start Now", callback_data="start_learning_now"),
            InlineKeyboardButton("⏰ Later", callback_data="start_learning_later")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
