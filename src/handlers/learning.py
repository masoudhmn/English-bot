"""
Learning session handlers for English Learning Bot.

This module handles:
- Starting learning sessions
- Showing words and collecting answers
- Difficulty rating
- Session completion
"""

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import select

from src.database import get_session
from src.models import Word, StudySession
from src.keyboards import (
    get_main_menu_keyboard,
    get_answer_keyboard,
    get_difficulty_keyboard,
    get_continue_keyboard,
)
from src.constants import SessionKey, Messages
from src.callback_data import (
    AnswerCallback,
    DifficultyCallback,
    NavigationCallback,
)
from src.services import create_study_session, record_review, end_session
from src.handlers.base import (
    get_session_value,
    set_session_value,
    clear_session_data,
    log_handler,
)
from src.logger import setup_logger

logger = setup_logger(__name__)


@log_handler("start_learning")
async def start_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start a new learning session.
    
    Retrieves words for review and new words based on user's daily limit.
    Creates a study session record in the database.
    """
    user_id = update.effective_user.id
    logger.info(f"User {user_id} starting learning session")
    
    # Get the message method (could be from callback or text)
    reply_func = (
        update.callback_query.message.reply_text 
        if update.callback_query 
        else update.message.reply_text
    )
    
    if update.callback_query:
        await update.callback_query.answer()
    
    try:
        async with get_session() as session:
            # Get user settings
            stmt = select(Word).where(Word.added_by == user_id)
            result = await session.execute(stmt)
            all_words = result.scalars().all()
            
            limit = 10  # Default limit for demo
            
            # Create study session using service
            session_id, review_word_ids, new_word_ids = await create_study_session(
                session, user_id, limit
            )
            
            # Check if there are any words to study
            if not review_word_ids and not new_word_ids:
                await reply_func(
                    Messages.NO_WORDS_TO_REVIEW,
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Store session data in context
            set_session_value(context, SessionKey.STUDY_SESSION_ID, session_id)
            set_session_value(context, SessionKey.WORDS_TO_REVIEW, review_word_ids)
            set_session_value(context, SessionKey.NEW_WORDS, new_word_ids)
            set_session_value(context, SessionKey.WORD_INDEX, 0)
            
            logger.info(f"Session created for user {user_id}: {session_id}")
        
        # Notify user about session
        total_words = len(review_word_ids) + len(new_word_ids)
        await reply_func(
            Messages.SESSION_STARTING.format(
                review_count=len(review_word_ids),
                new_count=len(new_word_ids),
                total_count=total_words
            )
        )
        
        # Show first word
        await show_next_word(update, context)
        
    except Exception as e:
        logger.error(f"Error starting learning session: {e}")
        await reply_func(Messages.ERROR_GENERIC)


@log_handler("show_next_word")
async def show_next_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the next word in the learning session.
    
    Determines if showing review word or new word,
    then presents it with answer buttons.
    """
    user_id = update.effective_user.id
    word_index = get_session_value(context, SessionKey.WORD_INDEX, 0)
    words_to_review = get_session_value(context, SessionKey.WORDS_TO_REVIEW, [])
    new_words = get_session_value(context, SessionKey.NEW_WORDS, [])
    
    total_words = len(words_to_review) + len(new_words)
    
    # Check if session is complete
    if word_index >= total_words:
        await end_learning_session(update, context)
        return
    
    try:
        async with get_session() as session:
            # Determine if showing review word or new word
            if word_index < len(words_to_review):
                word_id = words_to_review[word_index]
                is_new = False
            else:
                word_id = new_words[word_index - len(words_to_review)]
                is_new = True
            
            # Get word details from database
            stmt = select(Word).where(Word.id == word_id)
            result = await session.execute(stmt)
            word = result.scalar_one_or_none()
            
            if not word:
                logger.warning(f"Word {word_id} not found, skipping")
                set_session_value(context, SessionKey.WORD_INDEX, word_index + 1)
                await show_next_word(update, context)
                return
            
            # Store current word in session
            set_session_value(context, SessionKey.CURRENT_WORD, word_id)
            
            # Format word display
            word_type = "✨ New Word" if is_new else "🔄 Review"
            progress_text = f"Progress: {word_index + 1}/{total_words}"
            
            message = (
                f"{word_type} | {progress_text}\n\n"
                f"📝 Word: **{word.word}**\n\n"
                "Do you know the meaning?"
            )
            
            # Send or edit message based on update type
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    message,
                    reply_markup=get_answer_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=get_answer_keyboard(),
                    parse_mode="Markdown"
                )
                
    except Exception as e:
        logger.error(f"Error showing next word: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(Messages.ERROR_GENERIC)
        else:
            await update.message.reply_text(Messages.ERROR_GENERIC)


@log_handler("handle_answer")
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user's answer to whether they know the word.
    
    Parses the callback data, retrieves word details,
    and shows the answer with difficulty rating buttons.
    """
    query = update.callback_query
    await query.answer()
    
    word_id = get_session_value(context, SessionKey.CURRENT_WORD)
    
    if not word_id:
        await query.message.edit_text(Messages.ERROR_SESSION_EXPIRED)
        return
    
    # Parse callback data using type-safe handler
    callback = AnswerCallback.decode(query.data)
    if not callback:
        logger.error(f"Failed to parse answer callback: {query.data}")
        return
    
    is_correct = callback.is_correct
    
    try:
        async with get_session() as session:
            # Get word details
            stmt = select(Word).where(Word.id == word_id)
            result = await session.execute(stmt)
            word = result.scalar_one_or_none()
            
            if not word:
                await query.message.edit_text(Messages.ERROR_WORD_NOT_FOUND)
                return
            
            # Build answer message
            answer_emoji = "✅" if is_correct else "❌"
            message = (
                f"{answer_emoji} {'Correct!' if is_correct else 'Keep trying!'}\n\n"
                f"📝 **{word.word}**\n\n"
                f"📖 Definition:\n{word.definition}\n\n"
            )
            
            if word.example:
                message += f"💬 Example:\n_{word.example}_\n\n"
            
            if word.translation:
                message += f"🌐 Translation:\n{word.translation}\n\n"
            
            message += "How difficult is this word for you?"
            
            await query.message.edit_text(
                message,
                reply_markup=get_difficulty_keyboard(word_id, is_correct),
                parse_mode="Markdown"
            )
        
        # Store answer for later use
        set_session_value(context, SessionKey.LAST_ANSWER_CORRECT, is_correct)
        
    except Exception as e:
        logger.error(f"Error handling answer: {e}")
        await query.message.edit_text(Messages.ERROR_GENERIC)


@log_handler("handle_difficulty")
async def handle_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user's difficulty rating for a word.
    
    Updates word progress in the Leitner system and
    advances to the next word.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Parse callback data using type-safe handler
    callback = DifficultyCallback.decode(query.data)
    if not callback:
        logger.error(f"Failed to parse difficulty callback: {query.data}")
        await query.message.edit_text(
            Messages.ERROR_SESSION_EXPIRED,
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    word_id = callback.word_id
    is_correct = callback.is_correct
    difficulty = callback.difficulty.value
    
    try:
        async with get_session() as session:
            # Determine if this was a new word
            word_index = get_session_value(context, SessionKey.WORD_INDEX, 0)
            words_to_review = get_session_value(context, SessionKey.WORDS_TO_REVIEW, [])
            is_new = word_index >= len(words_to_review)
            
            session_id = get_session_value(context, SessionKey.STUDY_SESSION_ID)
            
            # Record review using service
            await record_review(
                session, session_id, word_id, user_id,
                is_correct, difficulty, is_new
            )
        
        # Advance to next word
        current_index = get_session_value(context, SessionKey.WORD_INDEX, 0)
        set_session_value(context, SessionKey.WORD_INDEX, current_index + 1)
        
        await query.message.edit_text(
            "Great! Moving to next word... ➡️",
            reply_markup=get_continue_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error handling difficulty: {e}")
        await query.message.edit_text(Messages.ERROR_GENERIC)


@log_handler("handle_next_word")
async def handle_next_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle navigation buttons (Next Word / Stop Learning).
    
    Parses callback to determine action and routes accordingly.
    """
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    callback = NavigationCallback.decode(query.data)
    if not callback:
        logger.error(f"Failed to parse navigation callback: {query.data}")
        return
    
    if callback.is_next_word:
        await show_next_word(update, context)
    elif callback.is_stop:
        await end_learning_session(update, context)


@log_handler("end_learning_session")
async def end_learning_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    End the current learning session.
    
    Updates session end time, calculates statistics,
    and displays session summary.
    """
    session_id = get_session_value(context, SessionKey.STUDY_SESSION_ID)
    summary = "Session ended."
    
    try:
        if session_id:
            async with get_session() as session:
                # End session using service
                stats = await end_session(session, session_id)
                
                if stats:
                    # Build summary message
                    summary = (
                        f"🎊 Session Complete!\n\n"
                        f"📊 Words Reviewed: {stats['words_reviewed']}\n"
                        f"✅ Correct: {stats['words_correct']}\n"
                        f"❌ Incorrect: {stats['words_incorrect']}\n"
                        f"✨ New Words: {stats['new_words']}\n"
                        f"🎯 Accuracy: {stats['accuracy']:.1f}%\n\n"
                        f"Great job! Keep it up! 💪"
                    )
                    
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        summary = "Session ended (with error saving stats)."
    
    # Clear session data
    clear_session_data(context)
    
    # Send summary based on update type
    if update.callback_query:
        await update.callback_query.message.edit_text(summary)
        await update.callback_query.message.reply_text(
            "What would you like to do next?",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(summary, reply_markup=get_main_menu_keyboard())
