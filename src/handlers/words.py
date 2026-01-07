"""
Word management handlers for English Learning Bot.

This module handles:
- Adding words via Excel upload
- Editing existing words
- Sample Excel template
"""

from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.database import get_session
from src.keyboards import get_main_menu_keyboard, get_edit_field_keyboard
from src.constants import ConversationState, SessionKey, Messages
from src.callback_data import EditFieldCallback
from src.excel_handler import process_excel_file, validate_excel_structure, create_sample_excel
from src.services import edit_word_field, get_word_by_text
from src.handlers.base import get_session_value, set_session_value, clear_session_data, log_handler
from src.logger import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# Add Words Handlers
# =============================================================================

@log_handler("add_words_prompt")
async def add_words_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Prompt user to upload an Excel file with words.
    
    Returns:
        WAITING_EXCEL_FILE state to handle file upload
    """
    await update.message.reply_text(Messages.PROMPT_UPLOAD_EXCEL)
    return ConversationState.WAITING_EXCEL_FILE


@log_handler("handle_excel_file")
async def handle_excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle uploaded Excel file with words.
    
    Validates the file structure, processes words,
    and reports results including duplicates.
    
    Returns:
        END on success, WAITING_EXCEL_FILE if validation fails
    """
    user_id = update.effective_user.id
    
    if not update.message or not update.message.document:
        await update.message.reply_text("❌ Please send an Excel file (.xlsx)")
        return ConversationState.WAITING_EXCEL_FILE
    
    # Create temp file path
    file = await update.message.document.get_file()
    file_path = Path(f"temp_{user_id}_{update.message.document.file_name}")
    
    try:
        await update.message.reply_text("⏳ Processing your file...")
        
        # Download file
        await file.download_to_drive(file_path)
        
        # Validate Excel structure
        is_valid, error_msg = validate_excel_structure(file_path)
        if not is_valid:
            await update.message.reply_text(f"❌ {error_msg}")
            return ConversationState.WAITING_EXCEL_FILE
        
        # Process file and add words
        async with get_session() as session:
            added_count, duplicates = await process_excel_file(session, file_path, user_id)
        
        # Build response message
        response = Messages.SUCCESS_WORDS_ADDED.format(count=added_count) + "\n\n"
        
        if duplicates:
            dup_list = ", ".join(duplicates[:10])
            if len(duplicates) > 10:
                dup_list += f" ... and {len(duplicates) - 10} more"
            response += f"⚠️ Duplicates skipped ({len(duplicates)}):\n{dup_list}"
        
        await update.message.reply_text(response, reply_markup=get_main_menu_keyboard())
        logger.info(f"User {user_id} added {added_count} words from Excel")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {e}")
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")
        return ConversationHandler.END
        
    finally:
        # Clean up temp file
        if file_path.exists():
            file_path.unlink()


@log_handler("send_sample_excel")
async def send_sample_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send a sample Excel template to the user.
    
    Creates a temporary file with sample data and sends it.
    """
    user_id = update.effective_user.id
    file_path = Path(f"sample_template_{user_id}.xlsx")
    
    try:
        # Create sample file
        create_sample_excel(file_path)
        
        # Send file to user
        await update.message.reply_document(
            document=file_path,
            filename="english_words_template.xlsx",
            caption="📖 Sample Excel Template\n\nUse this template to add your words!"
        )
        
    except Exception as e:
        logger.error(f"Error creating sample excel: {e}")
        await update.message.reply_text(f"❌ Error creating sample: {str(e)}")
        
    finally:
        # Clean up temp file
        if file_path.exists():
            file_path.unlink()


# =============================================================================
# Edit Word Handlers
# =============================================================================

@log_handler("edit_word_prompt")
async def edit_word_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Prompt user to enter the word they want to edit.
    
    Returns:
        WAITING_WORD_TO_EDIT state
    """
    await update.message.reply_text(Messages.PROMPT_EDIT_WORD)
    return ConversationState.WAITING_WORD_TO_EDIT


@log_handler("select_word_to_edit")
async def select_word_to_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle word selection for editing.
    
    Searches for the word in the database and shows
    current values with field selection buttons.
    
    Returns:
        END to allow field selection via callback, WAITING_WORD_TO_EDIT if not found
    """
    if not update.message or not update.message.text:
        return ConversationState.WAITING_WORD_TO_EDIT
    
    word_text = update.message.text.strip()
    
    try:
        async with get_session() as session:
            # Search for word using service
            word = await get_word_by_text(session, word_text)
            
            if not word:
                await update.message.reply_text(
                    f"❌ Word '{word_text}' not found.\n"
                    "Please try again or /cancel"
                )
                return ConversationState.WAITING_WORD_TO_EDIT
            
            # Store word ID for editing
            set_session_value(context, SessionKey.EDIT_WORD_ID, word.id)
            
            # Show current values
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
        
        # End conversation to let callback handler take over
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in select_word_to_edit: {e}")
        await update.message.reply_text(Messages.ERROR_GENERIC)
        return ConversationHandler.END


@log_handler("handle_edit_field_selection")
async def handle_edit_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle field selection for editing.
    
    Parses the callback to determine which field to edit
    and prompts user for new value.
    """
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    callback = EditFieldCallback.decode(query.data)
    if not callback:
        logger.error(f"Failed to parse edit callback: {query.data}")
        return
    
    # Handle cancel
    if callback.is_cancel:
        await query.message.edit_text(
            Messages.SUCCESS_OPERATION_CANCELLED,
            reply_markup=get_main_menu_keyboard()
        )
        clear_session_data(context, [SessionKey.EDIT_WORD_ID.value, SessionKey.EDIT_FIELD.value])
        return ConversationHandler.END 
    
    # Store field selection
    field = callback.field
    set_session_value(context, SessionKey.EDIT_FIELD, field)
    
    # Prompt for new value
    await query.message.edit_text(
        Messages.PROMPT_EDIT_VALUE.format(field=field),
        parse_mode="Markdown"
    )


@log_handler("handle_edit_value")
async def handle_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the new value input for word editing.
    
    Updates the word in the database using service.
    """
    if not update.message or not update.message.text:
        return
    
    new_value = update.message.text.strip()
    user_id = update.effective_user.id
    word_id = get_session_value(context, SessionKey.EDIT_WORD_ID)
    field = get_session_value(context, SessionKey.EDIT_FIELD)
    
    # Validate session data
    if not word_id or not field:
        await update.message.reply_text(Messages.ERROR_SESSION_EXPIRED)
        return
    
    try:
        async with get_session() as session:
            # Update word using service
            word = await edit_word_field(session, word_id, field, new_value, user_id)
            
            # Send success message
            await update.message.reply_text(
                Messages.SUCCESS_WORD_UPDATED.format(
                    word=word.word,
                    field=field,
                    value=new_value
                ),
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            logger.info(f"User {user_id} updated word {word.id} field {field}")
            
    except ValueError as e:
        await update.message.reply_text(str(e))
    except Exception as e:
        logger.error(f"Error updating word: {e}")
        await update.message.reply_text(Messages.ERROR_GENERIC)
    
    # Clear edit session data
    clear_session_data(context, [SessionKey.EDIT_WORD_ID.value, SessionKey.EDIT_FIELD.value])
