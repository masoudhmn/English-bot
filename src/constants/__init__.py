"""
Constants package for the English Learning Bot.

This package organizes all constants into logical modules:
- states: Conversation states and session keys
- messages: User-facing message templates
- buttons: Button text for keyboards
- callbacks: Callback data patterns
"""

from src.constants.states import ConversationState, SessionKey
from src.constants.messages import Messages
from src.constants.buttons import ButtonText, Difficulty
from src.constants.callbacks import CallbackAction, CallbackPrefix

__all__ = [
    "ConversationState",
    "SessionKey",
    "Messages",
    "ButtonText",
    "Difficulty",
    "CallbackAction",
    "CallbackPrefix",
]
