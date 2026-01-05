"""Main bot application"""
import logging
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

from src.config import TELEGRAM_BOT_TOKEN
from src.database import init_db, close_db
from src.scheduler import setup_daily_reminder

# Ensure 'set_reminder_time' is imported here!
from src.handlers import (
    start_command,
    set_word_limit,
    start_learning,
    handle_answer,
    handle_difficulty,
    handle_next_word,
    show_progress,
    add_words_prompt,
    handle_excel_file,
    send_sample_excel,
    edit_word_prompt,
    select_word_to_edit,
    handle_edit_field_selection,
    handle_edit_value,
    show_settings,
    cancel_command,
    handle_settings_buttons,
    set_reminder_time,  # <--- ADDED THIS
    WAITING_WORD_LIMIT,
    WAITING_EXCEL_FILE,
    WAITING_WORD_TO_EDIT,
    SESSION_EDIT_FIELD,
    SETTINGS_MENU,
    WAITING_REMINDER_TIME
)

from src.logger import setup_logger

# Configure logging
logger = setup_logger(__name__)

async def handle_text_message_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper for text message handler to keep imports clean"""
    
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    
    # Note: "⚙️ Settings" is NOT here anymore because 
    # settings_conv_handler catches it via entry_points.

    if text == "📚 Start Learning":
        await start_learning(update, context)
    elif text == "📊 My Progress":
        await show_progress(update, context)
    elif text == "➕ Add Words":
        return await add_words_prompt(update, context)
    elif text == "✏️ Edit Word":
        return await edit_word_prompt(update, context)
    elif text == "📖 Sample Excel":
        await send_sample_excel(update, context)
    else:
        # Check if user is in edit mode (fallback for complex edit flows)
        if context.user_data and SESSION_EDIT_FIELD in context.user_data:
            await handle_edit_value(update, context)
        else:
            await update.message.reply_text(
                "Please use the menu buttons below to navigate the bot."
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
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add Life Cycle Hooks
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    # --- Conversation Handlers ---

    start_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            WAITING_WORD_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_word_limit)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    
    add_words_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Add Words$"), add_words_prompt),
        ],
        states={
            WAITING_EXCEL_FILE: [MessageHandler(filters.Document.FileExtension("xlsx"), handle_excel_file)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    
    edit_word_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^✏️ Edit Word$"), edit_word_prompt),
        ],
        states={
            WAITING_WORD_TO_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_word_to_edit)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )

    settings_conv_handler = ConversationHandler(
        entry_points=[
            # This captures the "⚙️ Settings" button click
            MessageHandler(filters.Regex("^⚙️ Settings$"), show_settings)
        ],
        states={
            # State 1: User is looking at the buttons
            SETTINGS_MENU: [
                CallbackQueryHandler(handle_settings_buttons, pattern="^settings_")
            ],
            # State 2: User clicked "Set Limit" and needs to type a number
            WAITING_WORD_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_word_limit)
            ],
            # State 3: User clicked "Set Time" and needs to type time
            WAITING_REMINDER_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_time)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            # Catches the "Back" button if it sends 'settings_back'
            CallbackQueryHandler(handle_settings_buttons, pattern="^settings_back")
        ],
    )
    
    # --- Add Handlers (Order matters!) ---
    application.add_handler(start_conv_handler)
    application.add_handler(add_words_conv_handler)
    application.add_handler(edit_word_conv_handler)
    application.add_handler(settings_conv_handler) # Added Settings Handler here
    
    # Command handlers
    application.add_handler(CommandHandler("sample", send_sample_excel))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Callback query handlers (for buttons NOT in conversations)
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_"))
    application.add_handler(CallbackQueryHandler(handle_difficulty, pattern="^difficulty_"))
    application.add_handler(CallbackQueryHandler(handle_next_word, pattern="^(next_word|stop_learning)$"))
    application.add_handler(CallbackQueryHandler(handle_edit_field_selection, pattern="^edit_"))
    application.add_handler(CallbackQueryHandler(start_learning, pattern="^start_learning_now$"))
    
    # General Text Handler (Must be LAST to catch unmatched text)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message_wrapper))
    
    return application

def run_bot():
    """Run the bot"""
    logger.info("Starting English Learning Bot...")
    
    try:
        application = create_application()
        
        # Run the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Fatal error starting bot: {e}")
        raise

if __name__ == "__main__":
    run_bot()
