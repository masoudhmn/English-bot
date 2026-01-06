"""
Progress and statistics handlers for the English Learning Bot.

This module handles:
- Displaying user learning statistics
- Progress tracking and visualization
"""

from telegram import Update
from telegram.ext import ContextTypes

from src.database import get_session
from src.keyboards import get_main_menu_keyboard
from src.constants import Messages
from src.leitner import get_user_statistics
from src.handlers.base import log_handler
from src.logger import setup_logger

logger = setup_logger(__name__)


@log_handler("show_progress")
async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the user's learning progress and statistics.
    
    Shows:
    - Total words and mastered count
    - Due words for today
    - Review statistics (correct/incorrect/accuracy)
    - Leitner box distribution
    """
    user_id = update.effective_user.id
    
    try:
        async with get_session() as session:
            # Get user statistics from Leitner module
            stats = await get_user_statistics(session, user_id)
            
            # Format Leitner box distribution
            box_distribution = stats.get("box_distribution", {})
            box_lines = []
            for box, count in box_distribution.items():
                if count > 0:
                    # Add visual indicator based on box number
                    level = _get_level_indicator(box)
                    box_lines.append(f"  Box {box} {level}: {count} words")
            
            box_text = "\n".join(box_lines) if box_lines else "  No words yet"
            
            # Build progress message
            message = (
                f"📊 *Your Learning Progress*\n\n"
                f"📚 Total Words: {stats['total_words']}\n"
                f"🏆 Mastered: {stats['mastered_words']}\n"
                f"📅 Due Today: {stats['due_today']}\n\n"
                f"📈 *Statistics*\n"
                f"  Total Reviews: {stats['total_reviews']}\n"
                f"  ✅ Correct: {stats['total_correct']}\n"
                f"  ❌ Incorrect: {stats['total_incorrect']}\n"
                f"  🎯 Accuracy: {stats['accuracy']}%\n\n"
                f"📦 *Leitner Boxes*\n{box_text}"
            )
            
            await update.message.reply_text(
                message,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Error showing progress: {e}")
        await update.message.reply_text(
            Messages.ERROR_GENERIC,
            reply_markup=get_main_menu_keyboard()
        )


def _get_level_indicator(box: int) -> str:
    """
    Get a visual indicator for the Leitner box level.
    
    Args:
        box: Leitner box number (1-7)
        
    Returns:
        Emoji indicator representing proficiency level
    """
    indicators = {
        1: "🔴",  # New/needs work
        2: "🟠",  # Learning
        3: "🟡",  # Improving
        4: "🟢",  # Good
        5: "🔵",  # Great
        6: "🟣",  # Excellent
        7: "⭐",  # Mastered
    }
    return indicators.get(box, "⚪")
