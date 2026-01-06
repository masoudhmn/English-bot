"""
Main bot application
Entry point for the English Learning Telegram Bot.
"""

import logging
import os

# --- Telegram Imports ---
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# --- Configuration & Database ---
from src.config import TELEGRAM_BOT_TOKEN
from src.database import init_db, close_db
from src.scheduler import setup_daily_reminder
from src.logger import setup_logger

# --- Handlers & States ---
from src.handlers import (
    # Commands & Entry Points
    start_command,
    cancel_command,
    start_learning,
    show_progress,
    add_words_prompt,
    edit_word_prompt,
    show_settings,
    send_sample_excel,
    
    # Logic Handlers
    set_word_limit,
    handle_answer,
    handle_difficulty,
    handle_next_word,
    handle_excel_file,
    select_word_to_edit,
    handle_edit_field_selection,
    handle_edit_value,
    handle_settings_buttons,
    set_reminder_time,
    
    # States
    WAITING_WORD_LIMIT,
    WAITING_EXCEL_FILE,
    WAITING_WORD_TO_EDIT,
    SESSION_EDIT_FIELD,
    SETTINGS_MENU,
    WAITING_REMINDER_TIME
)

# Configure logging
logger = setup_logger(__name__)

async def handle_text_message_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Catch-all wrapper for text messages that are NOT caught by ConversationHandlers.
    
    NOTE: Messages like '➕ Add Words' or '⚙️ Settings' do NOT reach here 
    because they are consumed by the ConversationHandlers defined in create_application.
    """
    
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    
    # Simple Text Commands (that don't start a conversation)
    if text == "📚 Start Learning":
        await start_learning(update, context)
        
    elif text == "📊 My Progress":
        await show_progress(update, context)
        
    elif text == "📖 Sample Excel":
        await send_sample_excel(update, context)
        
    else:
        # Fallback: Check if user is in a manual 'Edit Mode' (outside of conv handler)
        if context.user_data and SESSION_EDIT_FIELD in context.user_data:
            await handle_edit_value(update, context)
        else:
            # If text matches nothing, show a helpful hint
            await update.message.reply_text(
                "I didn't understand that. Please use the menu buttons below."
            )
    
    return ConversationHandler.END

async def post_init(application: Application):
    """Initialize database and scheduler after bot starts"""
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Setting up daily reminders...")
    setup_daily_reminder(application)
    logger.info("Scheduler setup complete!")

async def post_shutdown(application: Application):
    """Cleanup on shutdown"""
    logger.info("Shutting down bot...")
    await close_db()
    logger.info("Database connections closed.")

def create_application():
    """Create and configure the bot application"""
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set")
        raise ValueError("TELEGRAM_BOT_TOKEN is missing from environment variables")
    
    # 1. Build Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 2. Add Life Cycle Hooks
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    # --- CONVERSATION HANDLERS ---
    
    # Handler: Start / Word Limit
    start_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            WAITING_WORD_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_word_limit)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    
    # Handler: Add Words via Excel
    add_words_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Add Words$"), add_words_prompt),
        ],
        states={
            WAITING_EXCEL_FILE: [MessageHandler(filters.Document.FileExtension("xlsx"), handle_excel_file)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    
    # Handler: Edit Word Flow
    edit_word_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^✏️ Edit Word$"), edit_word_prompt),
        ],
        states={
            WAITING_WORD_TO_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_word_to_edit)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    
    # Handler: Settings (With per_message=True to fix callback warnings)
    settings_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^⚙️ Settings$"), show_settings)
        ],
        states={
            SETTINGS_MENU: [
                CallbackQueryHandler(handle_settings_buttons, pattern="^settings_")
            ],
            WAITING_WORD_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_word_limit)
            ],
            WAITING_REMINDER_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_time)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(handle_settings_buttons, pattern="^settings_back")
        ],
        # per_message=True,  # Crucial for inline keyboard menus to avoid warnings
    )
    
    # --- REGISTER HANDLERS ---
    # NOTE: The order is critical. ConversationHandlers must be added BEFORE the fallback text handler.
    
    application.add_handler(start_conv_handler)
    application.add_handler(add_words_conv_handler)
    application.add_handler(edit_word_conv_handler)
    application.add_handler(settings_conv_handler)
    
    # Command Handlers
    application.add_handler(CommandHandler("sample", send_sample_excel))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Callback Query Handlers (Inline Buttons logic outside conversations)
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_"))
    application.add_handler(CallbackQueryHandler(handle_difficulty, pattern="^difficulty_"))
    application.add_handler(CallbackQueryHandler(handle_next_word, pattern="^(next_word|stop_learning)$"))
    application.add_handler(CallbackQueryHandler(handle_edit_field_selection, pattern="^edit_"))
    application.add_handler(CallbackQueryHandler(start_learning, pattern="^start_learning_now$"))
    
    # Fallback Text Handler (MUST BE LAST)
    # Catches "Start Learning", "My Progress", and unrecognized text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message_wrapper))
    
    return application

def run_bot():
    """Run the bot"""
    logger.info("Starting English Learning Bot...")
    try:
        application = create_application()
        # allowed_updates ensures we get all relevant events
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Fatal error starting bot: {e}")
        raise

if __name__ == "__main__":
    run_bot()