"""
Callback data patterns for inline buttons.
"""

from enum import Enum, auto


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
