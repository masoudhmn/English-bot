"""
Callback data handling module for the English Learning Bot.

This module provides type-safe callback data creation and parsing,
eliminating string manipulation errors and providing clear structure.
"""

from dataclasses import dataclass
from typing import Optional, Union
from enum import Enum

from src.constants import CallbackAction, Difficulty


# Separator used in callback data (Telegram limit is 64 bytes)
CALLBACK_SEPARATOR = ":"


@dataclass(frozen=True)
class AnswerCallback:
    """Callback data for answer buttons (I Know / I Don't Know)."""
    is_correct: bool
    
    def encode(self) -> str:
        """Encode to callback data string."""
        action = CallbackAction.ANSWER_CORRECT if self.is_correct else CallbackAction.ANSWER_INCORRECT
        return action.value
    
    @classmethod
    def decode(cls, data: str) -> Optional["AnswerCallback"]:
        """Decode from callback data string."""
        if data == CallbackAction.ANSWER_CORRECT.value:
            return cls(is_correct=True)
        elif data == CallbackAction.ANSWER_INCORRECT.value:
            return cls(is_correct=False)
        return None
    
    @staticmethod
    def pattern() -> str:
        """Regex pattern for CallbackQueryHandler."""
        return r"^answer:(correct|incorrect)$"


@dataclass(frozen=True)
class DifficultyCallback:
    """Callback data for difficulty rating buttons."""
    difficulty: Difficulty
    word_id: int
    is_correct: bool
    
    def encode(self) -> str:
        """Encode to callback data string."""
        correct_flag = "1" if self.is_correct else "0"
        return f"difficulty:{self.difficulty.value}:{self.word_id}:{correct_flag}"
    
    @classmethod
    def decode(cls, data: str) -> Optional["DifficultyCallback"]:
        """Decode from callback data string."""
        try:
            parts = data.split(CALLBACK_SEPARATOR)
            if len(parts) != 4 or parts[0] != "difficulty":
                return None
            
            difficulty = Difficulty(parts[1])
            word_id = int(parts[2])
            is_correct = parts[3] == "1"
            
            return cls(difficulty=difficulty, word_id=word_id, is_correct=is_correct)
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def pattern() -> str:
        """Regex pattern for CallbackQueryHandler."""
        return r"^difficulty:(easy|normal|hard):\d+:[01]$"


@dataclass(frozen=True)
class NavigationCallback:
    """Callback data for navigation buttons (Next Word / Stop Learning)."""
    action: str  # "word" or "stop"
    
    def encode(self) -> str:
        """Encode to callback data string."""
        return f"next:{self.action}"
    
    @classmethod
    def decode(cls, data: str) -> Optional["NavigationCallback"]:
        """Decode from callback data string."""
        try:
            parts = data.split(CALLBACK_SEPARATOR)
            if len(parts) != 2 or parts[0] != "next":
                return None
            return cls(action=parts[1])
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def pattern() -> str:
        """Regex pattern for CallbackQueryHandler."""
        return r"^next:(word|stop)$"
    
    @property
    def is_next_word(self) -> bool:
        return self.action == "word"
    
    @property
    def is_stop(self) -> bool:
        return self.action == "stop"


@dataclass(frozen=True)
class StartLearningCallback:
    """Callback data for start learning buttons."""
    action: str  # "now" or "later"
    
    def encode(self) -> str:
        """Encode to callback data string."""
        return f"start:{self.action}"
    
    @classmethod
    def decode(cls, data: str) -> Optional["StartLearningCallback"]:
        """Decode from callback data string."""
        try:
            parts = data.split(CALLBACK_SEPARATOR)
            if len(parts) != 2 or parts[0] != "start":
                return None
            return cls(action=parts[1])
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def pattern() -> str:
        """Regex pattern for CallbackQueryHandler."""
        return r"^start:(now|later)$"
    
    @property
    def is_now(self) -> bool:
        return self.action == "now"


@dataclass(frozen=True)
class EditFieldCallback:
    """Callback data for edit field selection buttons."""
    field: str  # "word", "definition", "example", "translation", or "cancel"
    
    def encode(self) -> str:
        """Encode to callback data string."""
        return f"edit:{self.field}"
    
    @classmethod
    def decode(cls, data: str) -> Optional["EditFieldCallback"]:
        """Decode from callback data string."""
        try:
            parts = data.split(CALLBACK_SEPARATOR)
            if len(parts) != 2 or parts[0] != "edit":
                return None
            return cls(field=parts[1])
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def pattern() -> str:
        """Regex pattern for CallbackQueryHandler."""
        return r"^edit:(word|definition|example|translation|cancel)$"
    
    @property
    def is_cancel(self) -> bool:
        return self.field == "cancel"


@dataclass(frozen=True)
class SettingsCallback:
    """Callback data for settings menu buttons."""
    action: str  # "limit", "reminder", "time", or "back"
    
    def encode(self) -> str:
        """Encode to callback data string."""
        return f"settings:{self.action}"
    
    @classmethod
    def decode(cls, data: str) -> Optional["SettingsCallback"]:
        """Decode from callback data string."""
        try:
            parts = data.split(CALLBACK_SEPARATOR)
            if len(parts) != 2 or parts[0] != "settings":
                return None
            return cls(action=parts[1])
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def pattern() -> str:
        """Regex pattern for CallbackQueryHandler."""
        return r"^settings:(limit|reminder|time|back)$"
    
    @property
    def is_back(self) -> bool:
        return self.action == "back"
    
    @property
    def is_limit(self) -> bool:
        return self.action == "limit"
    
    @property
    def is_reminder(self) -> bool:
        return self.action == "reminder"
    
    @property
    def is_time(self) -> bool:
        return self.action == "time"


@dataclass(frozen=True)
class ConfirmCallback:
    """Callback data for confirmation buttons."""
    confirmed: bool
    
    def encode(self) -> str:
        """Encode to callback data string."""
        return f"confirm:{'yes' if self.confirmed else 'no'}"
    
    @classmethod
    def decode(cls, data: str) -> Optional["ConfirmCallback"]:
        """Decode from callback data string."""
        try:
            parts = data.split(CALLBACK_SEPARATOR)
            if len(parts) != 2 or parts[0] != "confirm":
                return None
            return cls(confirmed=parts[1] == "yes")
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def pattern() -> str:
        """Regex pattern for CallbackQueryHandler."""
        return r"^confirm:(yes|no)$"


# Type alias for all callback types
CallbackData = Union[
    AnswerCallback,
    DifficultyCallback,
    NavigationCallback,
    StartLearningCallback,
    EditFieldCallback,
    SettingsCallback,
    ConfirmCallback,
]


def parse_callback_data(data: str) -> Optional[CallbackData]:
    """
    Parse callback data string into appropriate callback object.
    
    Args:
        data: Raw callback data string from Telegram
        
    Returns:
        Parsed callback object or None if parsing fails
    """
    if not data:
        return None
    
    prefix = data.split(CALLBACK_SEPARATOR)[0] if CALLBACK_SEPARATOR in data else data
    
    parsers = {
        "answer": AnswerCallback.decode,
        "difficulty": DifficultyCallback.decode,
        "next": NavigationCallback.decode,
        "start": StartLearningCallback.decode,
        "edit": EditFieldCallback.decode,
        "settings": SettingsCallback.decode,
        "confirm": ConfirmCallback.decode,
    }
    
    parser = parsers.get(prefix)
    if parser:
        return parser(data)
    
    return None
