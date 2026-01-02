"""Telegram bot handlers"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import select, and_

from src.database import get_db_session
from src.models import User, Word, StudySession, UserWordProgress, WordEditHistory
from src.leitner import get_words_for_review, get_new_words, update_word_progress, get_user_statistics
from src.excel_handler import process_excel_file, validate_excel_structure, create_sample_excel
from src.keyboards import (
    get_main_menu_keyboard,
    get_answer_keyboard,
    get_difficulty_keyboard,
    get_continue_keyboard,
    get_edit_field_keyboard,
    get_settings_keyboard,
    get_start_learning_keyboard,
)

# Conversation states
WAITING_WORD_LIMIT = 1
WAITING_EXCEL_FILE = 2
WAITING_WORD_TO_EDIT = 3
WAITING_EDIT_VALUE = 4
WAITING_REMINDER_TIME = 5

# User session data keys
SESSION_CURRENT_WORD = "current_word"
SESSION_STUDY_SESSION = "study_session"
SESSION_WORDS_TO_REVIEW = "words_to_review"
SESSION_NEW_WORDS = "new_words"
SESSION_WORD_INDEX = "word_index"
SESSION_EDIT_WORD_ID = "edit_word_id"
SESSION_EDIT_FIELD = "edit_field"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    async with get_db_session() as session:
        # Get or create user
        stmt = select(User).where(User.id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(db_user)
            await session.commit()
            
            welcome_message = (
                f"👋 Welcome {user.first_name}!\n\n"
                "🎯 I'm your English Learning Bot using the Leitner study method!\n\n"
                "📝 First, let's set your daily word limit.\n"
                "How many words would you like to practice each day?"
            )
            await update.message.reply_text(welcome_message)
            return WAITING_WORD_LIMIT
        else:
            # Update user info
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.last_active = datetime.utcnow()
            await session.commit()
    
    welcome_back = (
        f"👋 Welcome back, {user.first_name}!\n\n"
        "Choose an option from the menu below:"
    )
    await update.message.reply_text(
        welcome_back,
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def set_word_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting daily word limit"""
    try:
        limit = int(update.message.text)
        if limit < 1 or limit > 100:
            await update.message.reply_text(
                "❌ Please enter a number between 1 and 100."
            )
            return WAITING_WORD_LIMIT
        
        user_id = update.effective_user.id
        async with get_db_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if db_user:
                db_user.daily_word_limit = limit
                await session.commit()
        
        await update.message.reply_text(
            f"✅ Great! You'll practice {limit} words per day.\n\n"
            "Use the menu below to get started!",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number."
        )
        return WAITING_WORD_LIMIT


async def start_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a learning session"""
    user_id = update.effective_user.id
    
    async with get_db_session() as session:
        # Get user settings
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return
        
        limit = db_user.daily_word_limit
        
        # Get words for review
        words_to_review = await get_words_for_review(session, user_id, limit)
        
        # Calculate how many new words to show
        remaining_slots = limit - len(words_to_review)
        new_words = []
        if remaining_slots > 0:
            new_words = await get_new_words(session, user_id, remaining_slots)
        
        if not words_to_review and not new_words:
            await update.message.reply_text(
                "🎉 Great job! You have no words to review today.\n"
                "Add more words or come back tomorrow!",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Create study session
        study_session = StudySession(user_id=user_id)
        session.add(study_session)
        await session.commit()
        await session.refresh(study_session)
        
        # Store session data
        context.user_data[SESSION_STUDY_SESSION] = study_session.id
        context.user_data[SESSION_WORDS_TO_REVIEW] = [w.word_id for w in words_to_review]
        context.user_data[SESSION_NEW_WORDS] = [w.id for w in new_words]
        context.user_data[SESSION_WORD_INDEX] = 0
    
    total_words = len(words_to_review) + len(new_words)
    await update.message.reply_text(
        f"📚 Starting learning session!\n"
        f"📊 Review: {len(words_to_review)} words\n"
        f"✨ New: {len(new_words)} words\n"
        f"📈 Total: {total_words} words\n\n"
        "Let's begin! 🚀"
    )
    
    # Show first word
    await show_next_word(update, context)


async def show_next_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the next word in the learning session"""
    user_id = update.effective_user.id
    word_index = context.user_data.get(SESSION_WORD_INDEX, 0)
    words_to_review = context.user_data.get(SESSION_WORDS_TO_REVIEW, [])
    new_words = context.user_data.get(SESSION_NEW_WORDS, [])
    
    total_words = len(words_to_review) + len(new_words)
    
    if word_index >= total_words:
        # Session complete
        await end_learning_session(update, context)
        return
    
    async with get_db_session() as session:
        # Determine if showing review or new word
        if word_index < len(words_to_review):
            word_id = words_to_review[word_index]
            is_new = False
        else:
            word_id = new_words[word_index - len(words_to_review)]
            is_new = True
        
        # Get word details
        stmt = select(Word).where(Word.id == word_id)
        result = await session.execute(stmt)
        word = result.scalar_one_or_none()
        
        if not word:
            context.user_data[SESSION_WORD_INDEX] = word_index + 1
            await show_next_word(update, context)
            return
        
        context.user_data[SESSION_CURRENT_WORD] = word_id
        
        # Format word display
        word_type = "✨ New Word" if is_new else "🔄 Review"
        progress_text = f"Progress: {word_index + 1}/{total_words}"
        
        message = (
            f"{word_type} | {progress_text}\n\n"
            f"📝 Word: **{word.word}**\n\n"
            "Do you know the meaning?"
        )
        
        # Use callback query if available (for inline buttons)
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


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's answer to whether they know the word"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    word_id = context.user_data.get(SESSION_CURRENT_WORD)
    is_correct = query.data == "answer_correct"
    
    if not word_id:
        await query.message.reply_text("❌ Error: No current word found.")
        return
    
    async with get_db_session() as session:
        # Get word details
        stmt = select(Word).where(Word.id == word_id)
        result = await session.execute(stmt)
        word = result.scalar_one_or_none()
        
        if not word:
            await query.message.reply_text("❌ Word not found.")
            return
        
        # Show the answer
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
            reply_markup=get_difficulty_keyboard(),
            parse_mode="Markdown"
        )
    
    # Store the answer
    context.user_data["last_answer_correct"] = is_correct


async def handle_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's difficulty rating"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    word_id = context.user_data.get(SESSION_CURRENT_WORD)
    is_correct = context.user_data.get("last_answer_correct", False)
    
    # Extract difficulty from callback data
    difficulty_map = {
        "difficulty_easy": "easy",
        "difficulty_normal": "normal",
        "difficulty_hard": "hard"
    }
    difficulty = difficulty_map.get(query.data)
    
    async with get_db_session() as session:
        # Update word progress
        await update_word_progress(session, user_id, word_id, is_correct, difficulty)
        
        # Update study session stats
        session_id = context.user_data.get(SESSION_STUDY_SESSION)
        if session_id:
            stmt = select(StudySession).where(StudySession.id == session_id)
            result = await session.execute(stmt)
            study_session = result.scalar_one_or_none()
            
            if study_session:
                study_session.words_reviewed += 1
                if is_correct:
                    study_session.words_correct += 1
                else:
                    study_session.words_incorrect += 1
                
                # Check if it's a new word
                word_index = context.user_data.get(SESSION_WORD_INDEX, 0)
                words_to_review = context.user_data.get(SESSION_WORDS_TO_REVIEW, [])
                if word_index >= len(words_to_review):
                    study_session.new_words += 1
                
                await session.commit()
    
    # Move to next word
    context.user_data[SESSION_WORD_INDEX] = context.user_data.get(SESSION_WORD_INDEX, 0) + 1
    
    await query.message.edit_text(
        "Great! Moving to next word... ➡️",
        reply_markup=get_continue_keyboard()
    )


async def handle_next_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle next word button"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "next_word":
        await show_next_word(update, context)
    elif query.data == "stop_learning":
        await end_learning_session(update, context)


async def end_learning_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End the current learning session"""
    user_id = update.effective_user.id
    session_id = context.user_data.get(SESSION_STUDY_SESSION)
    
    async with get_db_session() as session:
        if session_id:
            stmt = select(StudySession).where(StudySession.id == session_id)
            result = await session.execute(stmt)
            study_session = result.scalar_one_or_none()
            
            if study_session:
                study_session.ended_at = datetime.utcnow()
                await session.commit()
                
                # Show session summary
                accuracy = 0
                if study_session.words_reviewed > 0:
                    accuracy = (study_session.words_correct / study_session.words_reviewed) * 100
                
                summary = (
                    f"🎊 Session Complete!\n\n"
                    f"📊 Words Reviewed: {study_session.words_reviewed}\n"
                    f"✅ Correct: {study_session.words_correct}\n"
                    f"❌ Incorrect: {study_session.words_incorrect}\n"
                    f"✨ New Words: {study_session.new_words}\n"
                    f"🎯 Accuracy: {accuracy:.1f}%\n\n"
                    f"Great job! Keep it up! 💪"
                )
            else:
                summary = "Session ended."
        else:
            summary = "Session ended."
    
    # Clear session data
    context.user_data.clear()
    
    # Use appropriate method based on update type
    if update.callback_query:
        await update.callback_query.message.edit_text(summary, reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(summary, reply_markup=get_main_menu_keyboard())


async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's progress statistics"""
    user_id = update.effective_user.id
    
    async with get_db_session() as session:
        stats = await get_user_statistics(session, user_id)
        
        # Format box distribution
        box_dist = "\n".join([
            f"Box {box}: {count} words" for box, count in stats["box_distribution"].items() if count > 0
        ])
        
        message = (
            f"📊 Your Learning Progress\n\n"
            f"📚 Total Words: {stats['total_words']}\n"
            f"🏆 Mastered: {stats['mastered_words']}\n"
            f"📅 Due Today: {stats['due_today']}\n\n"
            f"📈 Statistics:\n"
            f"Total Reviews: {stats['total_reviews']}\n"
            f"Correct: {stats['total_correct']}\n"
            f"Incorrect: {stats['total_incorrect']}\n"
            f"Accuracy: {stats['accuracy']}%\n\n"
            f"📦 Leitner Boxes:\n{box_dist if box_dist else 'No words yet'}"
        )
        
        await update.message.reply_text(message, reply_markup=get_main_menu_keyboard())


async def add_words_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to upload Excel file"""
    message = (
        "📤 Upload Excel File\n\n"
        "Send me an Excel file (.xlsx) with your words.\n\n"
        "Required columns:\n"
        "• word\n"
        "• definition\n\n"
        "Optional columns:\n"
        "• example\n"
        "• translation\n\n"
        "Use /sample to get a sample Excel template."
    )
    await update.message.reply_text(message)
    return WAITING_EXCEL_FILE


async def handle_excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded Excel file"""
    user_id = update.effective_user.id
    
    if not update.message.document:
        await update.message.reply_text("❌ Please send an Excel file (.xlsx)")
        return WAITING_EXCEL_FILE
    
    file = await update.message.document.get_file()
    file_path = Path(f"temp_{user_id}_{update.message.document.file_name}")
    
    try:
        await update.message.reply_text("⏳ Processing your file...")
        
        # Download file
        await file.download_to_drive(file_path)
        
        # Validate structure
        is_valid, error_msg = validate_excel_structure(file_path)
        if not is_valid:
            await update.message.reply_text(f"❌ {error_msg}")
            file_path.unlink()
            return WAITING_EXCEL_FILE
        
        # Process file
        async with get_db_session() as session:
            added_count, duplicates = await process_excel_file(session, file_path, user_id)
        
        # Build response message
        response = f"✅ Successfully added {added_count} words!\n\n"
        
        if duplicates:
            dup_list = ", ".join(duplicates[:10])
            if len(duplicates) > 10:
                dup_list += f" ... and {len(duplicates) - 10} more"
            response += f"⚠️ Duplicates skipped ({len(duplicates)}):\n{dup_list}"
        
        await update.message.reply_text(response, reply_markup=get_main_menu_keyboard())
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")
    finally:
        # Clean up temp file
        if file_path.exists():
            file_path.unlink()
    
    return ConversationHandler.END


async def send_sample_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send sample Excel template"""
    user_id = update.effective_user.id
    file_path = Path(f"sample_template_{user_id}.xlsx")
    
    try:
        create_sample_excel(file_path)
        await update.message.reply_document(
            document=file_path,
            filename="english_words_template.xlsx",
            caption="📖 Sample Excel Template\n\nUse this template to add your words!"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error creating sample: {str(e)}")
    finally:
        if file_path.exists():
            file_path.unlink()


async def edit_word_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to enter word to edit"""
    await update.message.reply_text(
        "✏️ Edit Word\n\n"
        "Enter the word you want to edit:"
    )
    return WAITING_WORD_TO_EDIT


async def select_word_to_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle word selection for editing"""
    word_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    async with get_db_session() as session:
        stmt = select(Word).where(Word.word.ilike(word_text))
        result = await session.execute(stmt)
        word = result.scalar_one_or_none()
        
        if not word:
            await update.message.reply_text(
                f"❌ Word '{word_text}' not found.\n"
                "Please try again or /cancel"
            )
            return WAITING_WORD_TO_EDIT
        
        context.user_data[SESSION_EDIT_WORD_ID] = word.id
        
        message = (
            f"📝 Editing: **{word.word}**\n\n"
            f"Definition: {word.definition}\n"
            f"Example: {word.example or 'N/A'}\n"
            f"Translation: {word.translation or 'N/A'}\n\n"
            "What do you want to edit?"
        )
        
        await update.message.reply_text(
            message,
            reply_markup=get_edit_field_keyboard(),
            parse_mode="Markdown"
        )
    
    return ConversationHandler.END


async def handle_edit_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection for editing"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "edit_cancel":
        await query.message.edit_text("✅ Edit cancelled.", reply_markup=get_main_menu_keyboard())
        return
    
    field_map = {
        "edit_field_word": "word",
        "edit_field_definition": "definition",
        "edit_field_example": "example",
        "edit_field_translation": "translation"
    }
    
    field = field_map.get(query.data)
    context.user_data[SESSION_EDIT_FIELD] = field
    
    await query.message.edit_text(
        f"✏️ Enter new value for **{field}**:",
        parse_mode="Markdown"
    )


async def handle_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new value for edited field"""
    new_value = update.message.text.strip()
    user_id = update.effective_user.id
    word_id = context.user_data.get(SESSION_EDIT_WORD_ID)
    field = context.user_data.get(SESSION_EDIT_FIELD)
    
    if not word_id or not field:
        await update.message.reply_text("❌ Error: Edit session expired.")
        return
    
    async with get_db_session() as session:
        stmt = select(Word).where(Word.id == word_id)
        result = await session.execute(stmt)
        word = result.scalar_one_or_none()
        
        if not word:
            await update.message.reply_text("❌ Word not found.")
            return
        
        # Get old value
        old_value = getattr(word, field)
        
        # Update word
        setattr(word, field, new_value)
        word.updated_at = datetime.utcnow()
        
        # Record edit history
        edit_history = WordEditHistory(
            word_id=word_id,
            edited_by=user_id,
            field_name=field,
            old_value=old_value,
            new_value=new_value
        )
        session.add(edit_history)
        
        await session.commit()
        
        await update.message.reply_text(
            f"✅ Updated **{word.word}**\n\n"
            f"{field}: {new_value}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    
    # Clear edit session
    context.user_data.pop(SESSION_EDIT_WORD_ID, None)
    context.user_data.pop(SESSION_EDIT_FIELD, None)


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    user_id = update.effective_user.id
    
    async with get_db_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text("❌ User not found.")
            return
        
        message = (
            f"⚙️ Settings\n\n"
            f"📈 Daily Word Limit: {user.daily_word_limit}\n"
            f"🔔 Reminder: {'Enabled' if user.reminder_enabled else 'Disabled'}\n"
            f"⏰ Reminder Time: {user.reminder_time}\n"
        )
        
        await update.message.reply_text(
            message,
            reply_markup=get_settings_keyboard(user.reminder_enabled)
        )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    await update.message.reply_text(
        "✅ Operation cancelled.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END
