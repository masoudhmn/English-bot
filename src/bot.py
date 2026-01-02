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
)

from src.config import TELEGRAM_BOT_TOKEN
from src.database import init_db, close_db
from src.scheduler import setup_daily_reminder
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
    WAITING_WORD_LIMIT,
    WAITING_EXCEL_FILE,
    WAITING_WORD_TO_EDIT,
    SESSION_EDIT_FIELD,
)
from src.logger import setup_logger

# Configure logging
logger = setup_logger(__name__)


async def handle_text_message_wrapper(update: Update, context):
    """Wrapper for text message handler to keep imports clean"""
    # Simply delegate to the handler in handlers.py
    # We need to implement handle_text_message in handlers.py or keep it here.
    # The original bot.py had it here. Let's see if handlers.py has it. 
    # I didn't verify if I kept handle_text_message in handlers.py.
    # Looking at my previous write_to_file for handlers.py, I did NOT include handle_text_message.
    # So I need to add it here or in handlers.py. 
    # It's better in handlers.py to keep bot.py clean.
    # I will implement it here for now to avoid modifying handlers.py again immediately, 
    # but strictly speaking it belongs to handlers.
    
    text = update.message.text
    
    if text == "📚 Start Learning":
        await start_learning(update, context)
    elif text == "📊 My Progress":
        await show_progress(update, context)
    elif text == "➕ Add Words":
        return await add_words_prompt(update, context)
    elif text == "✏️ Edit Word":
        return await edit_word_prompt(update, context)
    elif text == "⚙️ Settings":
        await show_settings(update, context)
    elif text == "📖 Sample Excel":
        await send_sample_excel(update, context)
    else:
        # Check if user is in edit mode
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
    
    # Add initialization and shutdown handlers
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    # Conversation handlers
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
    
    # Add handlers
    application.add_handler(start_conv_handler)
    application.add_handler(add_words_conv_handler)
    application.add_handler(edit_word_conv_handler)
    
    # Command handlers
    application.add_handler(CommandHandler("sample", send_sample_excel))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_"))
    application.add_handler(CallbackQueryHandler(handle_difficulty, pattern="^difficulty_"))
    application.add_handler(CallbackQueryHandler(handle_next_word, pattern="^(next_word|stop_learning)$"))
    application.add_handler(CallbackQueryHandler(handle_edit_field_selection, pattern="^edit_"))
    application.add_handler(CallbackQueryHandler(start_learning, pattern="^start_learning_now$"))
    
    # Text message handler (for menu buttons)
    # Using the local wrapper
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
