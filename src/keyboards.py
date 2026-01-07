"""
Telegram keyboard layouts for bot UI.

This module provides all keyboard builders using type-safe callback data
and centralized button text constants.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from src.constants import ButtonText, Difficulty
from src.callback_data import (
    AnswerCallback,
    DifficultyCallback,
    NavigationCallback,
    StartLearningCallback,
    EditFieldCallback,
    SettingsCallback,
    ConfirmCallback,
)


# =============================================================================
# Reply Keyboards (Persistent menu keyboards)
# =============================================================================

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Build the main menu reply keyboard.
    
    This keyboard persists at the bottom of the chat and provides
    quick access to all main features.
    """
    keyboard = [
        [
            KeyboardButton(ButtonText.START_LEARNING),
            KeyboardButton(ButtonText.MY_PROGRESS)
        ],
        [
            KeyboardButton(ButtonText.ADD_WORDS),
            KeyboardButton(ButtonText.EDIT_WORD)
        ],
        [
            KeyboardButton(ButtonText.SETTINGS),
            # KeyboardButton(ButtonText.SAMPLE_EXCEL)
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )

def get_edit_word_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Build the cancel edit word reply keyboard.
    
    This keyboard persists at the bottom of the chat and provides
    quick access to all main features.
    """
    keyboard = [
        [
            # KeyboardButton(ButtonText.CANCEL),
            KeyboardButton("/cancel"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )

# =============================================================================
# Inline Keyboards (Message-attached keyboards)
# =============================================================================

def get_answer_keyboard() -> InlineKeyboardMarkup:
    """
    Build the answer keyboard for "Do you know this word?" prompt.
    
    Returns:
        Inline keyboard with "I Know" and "I Don't Know" buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(
                ButtonText.I_KNOW,
                callback_data=AnswerCallback(is_correct=True).encode()
            ),
            InlineKeyboardButton(
                ButtonText.I_DONT_KNOW,
                callback_data=AnswerCallback(is_correct=False).encode()
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_difficulty_keyboard(word_id: int, is_correct: bool) -> InlineKeyboardMarkup:
    """
    Build the difficulty rating keyboard.
    
    Args:
        word_id: ID of the word being rated
        is_correct: Whether the user answered correctly
        
    Returns:
        Inline keyboard with difficulty options (Easy, Normal, Hard)
    """
    keyboard = [
        [
            InlineKeyboardButton(
                ButtonText.EASY,
                callback_data=DifficultyCallback(
                    difficulty=Difficulty.EASY,
                    word_id=word_id,
                    is_correct=is_correct
                ).encode()
            ),
            InlineKeyboardButton(
                ButtonText.NORMAL,
                callback_data=DifficultyCallback(
                    difficulty=Difficulty.NORMAL,
                    word_id=word_id,
                    is_correct=is_correct
                ).encode()
            ),
            InlineKeyboardButton(
                ButtonText.HARD,
                callback_data=DifficultyCallback(
                    difficulty=Difficulty.HARD,
                    word_id=word_id,
                    is_correct=is_correct
                ).encode()
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_continue_keyboard() -> InlineKeyboardMarkup:
    """
    Build the continue/stop keyboard for learning sessions.
    
    Returns:
        Inline keyboard with "Next Word" and "Stop Learning" buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(
                ButtonText.NEXT_WORD,
                callback_data=NavigationCallback(action="word").encode()
            ),
            InlineKeyboardButton(
                ButtonText.STOP_LEARNING,
                callback_data=NavigationCallback(action="stop").encode()
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_start_learning_keyboard() -> InlineKeyboardMarkup:
    """
    Build the start learning keyboard for reminders.
    
    Returns:
        Inline keyboard with "Start Now" and "Later" buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(
                ButtonText.START_NOW,
                callback_data=StartLearningCallback(action="now").encode()
            ),
            InlineKeyboardButton(
                ButtonText.LATER,
                callback_data=StartLearningCallback(action="later").encode()
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_field_keyboard() -> InlineKeyboardMarkup:
    """
    Build the edit field selection keyboard.
    
    Returns:
        Inline keyboard with field options (Word, Definition, Example, Translation)
        and a Cancel button
    """
    keyboard = [
        [
            InlineKeyboardButton(
                ButtonText.WORD,
                callback_data=EditFieldCallback(field="word").encode()
            ),
            InlineKeyboardButton(
                ButtonText.DEFINITION,
                callback_data=EditFieldCallback(field="definition").encode()
            )
        ],
        [
            InlineKeyboardButton(
                ButtonText.EXAMPLE,
                callback_data=EditFieldCallback(field="example").encode()
            ),
            InlineKeyboardButton(
                ButtonText.TRANSLATION,
                callback_data=EditFieldCallback(field="translation").encode()
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         ButtonText.CANCEL,
        #         callback_data=EditFieldCallback(field="cancel").encode()
        #     )
        # ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard(reminder_enabled: bool) -> InlineKeyboardMarkup:
    """
    Build the settings menu keyboard.
    
    Args:
        reminder_enabled: Current state of reminder setting
        
    Returns:
        Inline keyboard with settings options
    """
    reminder_text = ButtonText.DISABLE_REMINDER if reminder_enabled else ButtonText.ENABLE_REMINDER
    
    keyboard = [
        [
            InlineKeyboardButton(
                ButtonText.SET_DAILY_LIMIT,
                callback_data=SettingsCallback(action="limit").encode()
            )
        ],
        [
            InlineKeyboardButton(
                reminder_text,
                callback_data=SettingsCallback(action="reminder").encode()
            )
        ],
        [
            InlineKeyboardButton(
                ButtonText.SET_REMINDER_TIME,
                callback_data=SettingsCallback(action="time").encode()
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         ButtonText.BACK,
        #         callback_data=SettingsCallback(action="back").encode()
        #     )
        # ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Build a generic Yes/No confirmation keyboard.
    
    Returns:
        Inline keyboard with Yes and No buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(
                ButtonText.YES,
                callback_data=ConfirmCallback(confirmed=True).encode()
            ),
            InlineKeyboardButton(
                ButtonText.NO,
                callback_data=ConfirmCallback(confirmed=False).encode()
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# =============================================================================
# Keyboard Utilities
# =============================================================================

def remove_keyboard() -> None:
    """
    Return None to indicate keyboard should be removed.
    
    Use this when you want to remove the inline keyboard from a message.
    """
    return None
