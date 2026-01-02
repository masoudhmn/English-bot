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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """Initialize database and scheduler after bot starts"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized!")
    
    logger.info("Setting up daily reminders...")
    setup_daily_reminder(application)
    logger.info("Scheduler setup complete!")


async def post_shutdown(application: Application):
    """Cleanup on shutdown"""
    logger.info("Shutting down bot...")
    await close_db()
    logger.info("Database connections closed.")


async def handle_text_message(update: Update, context):
    """Handle text messages from main menu"""
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
        if SESSION_EDIT_FIELD in context.user_data:
            await handle_edit_value(update, context)
        else:
            await update.message.reply_text(
                "Please use the menu buttons below to navigate the bot."
            )
    
    return ConversationHandler.END


def create_application():
    """Create and configure the bot application"""
    
    if not TELEGRAM_BOT_TOKEN:
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    return application


def run_bot():
    """Run the bot"""
    logger.info("Starting English Learning Bot...")
    
    application = create_application()
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
