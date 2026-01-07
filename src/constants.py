"""
Constants module for the English Learning Bot.

This module now imports from the reorganized constants package.
All imports are maintained here for backward compatibility.
"""

# Import from the new package structure
from src.constants.states import ConversationState, SessionKey
from src.constants.messages import Messages
from src.constants.buttons import ButtonText, Difficulty
from src.constants.callbacks import CallbackPrefix, CallbackAction

__all__ = [
    "ConversationState",
    "SessionKey",
    "Messages",
    "ButtonText",
    "Difficulty",
    "CallbackPrefix",
    "CallbackAction",
]
