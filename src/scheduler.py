"""Daily reminder scheduler for the bot"""

from datetime import time
from telegram.ext import ContextTypes
from sqlalchemy import select

from src.database import get_db_session
from src.models import User
from src.keyboards import get_start_learning_keyboard


async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send daily learning reminder to users"""
    async with get_db_session() as session:
        # Get all active users with reminders enabled
        stmt = select(User).where(User.reminder_enabled == True, User.is_active == True)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        for user in users:
            try:
                message = (
                    f"🌟 Good morning, {user.first_name}!\n\n"
                    f"📚 It's time for your daily English practice!\n"
                    f"Ready to learn {user.daily_word_limit} words today?"
                )
                
                await context.bot.send_message(
                    chat_id=user.id,
                    text=message,
                    reply_markup=get_start_learning_keyboard()
                )
            except Exception as e:
                # User might have blocked the bot
                print(f"Failed to send reminder to user {user.id}: {e}")


def setup_daily_reminder(application):
    """Setup daily reminder job"""
    # Schedule reminder at 9:00 AM every day
    job_queue = application.job_queue
    
    # Run daily at 9:00 AM
    job_queue.run_daily(
        send_daily_reminder,
        time=time(hour=9, minute=0),
        name="daily_reminder"
    )
