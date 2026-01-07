"""
Services package for the English Learning Bot.

This package contains business logic services that handle:
- user_service: User management and registration
- word_service: Word management and editing
- learning_service: Learning session management
- progress_service: Statistics and progress tracking
"""

from src.services.user_service import (
    create_user,
    get_or_create_user,
    update_user_settings,
    toggle_reminder,
    set_reminder_time as set_user_reminder_time,
)
from src.services.word_service import (
    create_word_from_excel,
    edit_word_field,
    get_word_by_text,
)
from src.services.learning_service import (
    create_study_session,
    record_review,
    end_session,
)
from src.services.progress_service import get_user_statistics

__all__ = [
    # User service
    "create_user",
    "get_or_create_user",
    "update_user_settings",
    "toggle_reminder",
    "set_user_reminder_time",
    # Word service
    "create_word_from_excel",
    "edit_word_field",
    "get_word_by_text",
    # Learning service
    "create_study_session",
    "record_review",
    "end_session",
    # Progress service
    "get_user_statistics",
]
