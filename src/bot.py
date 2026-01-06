"""
Main bot application for the English Learning Bot.

This module is the entry point for the Telegram bot, handling:
- Application initialization and configuration
- Handler registration
- Lifecycle management (startup/shutdown)
"""

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
from src.logger import setup_logger

# Import constants
from src.constants import ConversationState, ButtonText, SessionKey

# Import callback patterns
from src.callback_data import (
    AnswerCallback,
    DifficultyCallback,
    NavigationCallback,
    StartLearningCallback,
    EditFieldCallback,
    SettingsCallback,
)

# Import handlers
from src.handlers import (
    # Error handler
    error_handler,
    
    # Start handlers
    start_command,
    set_word_limit,
    cancel_command,
    
    # Learning handlers
    start_learning,
    handle_answer,
    handle_difficulty,
    handle_next_word,
    
    # Word handlers
    add_words_prompt,
    handle_excel_file,
    send_sample_excel,
    edit_word_prompt,
    select_word_to_edit,
    handle_edit_field_selection,
    handle_edit_value,
    
    # Settings handlers
    show_settings,
    handle_settings_buttons,
    set_reminder_time,
    
    # Progress handlers
    show_progress,
)

from src.keyboards import get_main_menu_keyboard

logger = setup_logger(__name__)


# =============================================================================
# Text Message Router
# =============================================================================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Route text messages from the main menu keyboard.
    
    This handler catches text messages that are NOT consumed by ConversationHandlers
    and routes them to the appropriate feature handlers.
    
    NOTE: Messages matching ConversationHandler entry points (like "➕ Add Words")
    are consumed by those handlers and never reach here.
    """
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    
    # Route based on button text
    if text == ButtonText.START_LEARNING:
        await start_learning(update, context)
        
    elif text == ButtonText.MY_PROGRESS:
        await show_progress(update, context)
        
    elif text == ButtonText.SAMPLE_EXCEL:
        await send_sample_excel(update, context)
        
    else:
        # Check if user is in edit mode (waiting for new value)
        edit_field = context.user_data.get(SessionKey.EDIT_FIELD.value) if context.user_data else None
        if edit_field:
            await handle_edit_value(update, context)
        else:
            # Unknown message - show help
            await update.message.reply_text(
                "I didn't understand that. Please use the menu buttons below.",
                reply_markup=get_main_menu_keyboard()
            )
    
    return ConversationHandler.END


# =============================================================================
# Lifecycle Hooks
# =============================================================================

async def post_init(application: Application):
    """
    Initialize resources after the bot starts.
    
    - Initializes database connection and tables
    - Sets up the daily reminder scheduler
    """
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Setting up daily reminders...")
    setup_daily_reminder(application)
    logger.info("Bot initialization complete!")


async def post_shutdown(application: Application):
    """
    Clean up resources on shutdown.
    
    - Closes database connections
    """
    logger.info("Shutting down bot...")
    await close_db()
    logger.info("Bot shutdown complete.")


# =============================================================================
# Handler Registration
# =============================================================================

def _create_start_conversation() -> ConversationHandler:
    """Create the /start conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command)
        ],
        states={
            ConversationState.WAITING_WORD_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_word_limit)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        name="start_conversation",
        persistent=False,
    )


def _create_add_words_conversation() -> ConversationHandler:
    """Create the Add Words conversation handler."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(f"^{ButtonText.ADD_WORDS}$"),
                add_words_prompt
            ),
        ],
        states={
            ConversationState.WAITING_EXCEL_FILE: [
                MessageHandler(
                    filters.Document.FileExtension("xlsx"),
                    handle_excel_file
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        name="add_words_conversation",
        persistent=False,
    )


def _create_edit_word_conversation() -> ConversationHandler:
    """Create the Edit Word conversation handler."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(f"^{ButtonText.EDIT_WORD}$"),
                edit_word_prompt
            ),
        ],
        states={
            ConversationState.WAITING_WORD_TO_EDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_word_to_edit)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        name="edit_word_conversation",
        persistent=False,
    )


def _create_settings_conversation() -> ConversationHandler:
    """Create the Settings conversation handler."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(f"^{ButtonText.SETTINGS}$"),
                show_settings
            )
        ],
        states={
            ConversationState.SETTINGS_MENU: [
                CallbackQueryHandler(
                    handle_settings_buttons,
                    pattern=SettingsCallback.pattern()
                )
            ],
            ConversationState.WAITING_WORD_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_word_limit)
            ],
            ConversationState.WAITING_REMINDER_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_time)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(
                handle_settings_buttons,
                pattern=r"^settings:back$"
            )
        ],
        name="settings_conversation",
        persistent=False,
    )


def _register_handlers(application: Application) -> None:
    """
    Register all handlers with the application.
    
    Handler registration order is important:
    1. ConversationHandlers (highest priority, consume matching updates)
    2. Command handlers
    3. Callback query handlers (for inline buttons)
    4. Text message fallback handler (lowest priority)
    """
    
    # --- 1. Conversation Handlers ---
    # These must be registered first to properly consume their entry point messages
    
    application.add_handler(_create_start_conversation())
    application.add_handler(_create_add_words_conversation())
    application.add_handler(_create_edit_word_conversation())
    application.add_handler(_create_settings_conversation())
    
    # --- 2. Command Handlers ---
    
    application.add_handler(CommandHandler("sample", send_sample_excel))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("progress", show_progress))
    application.add_handler(CommandHandler("learn", start_learning))
    
    # --- 3. Callback Query Handlers ---
    # For inline buttons outside of conversation handlers
    
    # Learning flow callbacks
    application.add_handler(
        CallbackQueryHandler(handle_answer, pattern=AnswerCallback.pattern())
    )
    application.add_handler(
        CallbackQueryHandler(handle_difficulty, pattern=DifficultyCallback.pattern())
    )
    application.add_handler(
        CallbackQueryHandler(handle_next_word, pattern=NavigationCallback.pattern())
    )
    
    # Start learning from reminder
    application.add_handler(
        CallbackQueryHandler(start_learning, pattern=StartLearningCallback.pattern())
    )
    
    # Edit word field selection
    application.add_handler(
        CallbackQueryHandler(handle_edit_field_selection, pattern=EditFieldCallback.pattern())
    )
    
    # --- 4. Text Message Fallback Handler ---
    # MUST be last - catches all unhandled text messages
    
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    
    # --- 5. Error Handler ---
    
    application.add_error_handler(error_handler)
    
    logger.info("All handlers registered successfully")


# =============================================================================
# Application Factory
# =============================================================================

def create_application() -> Application:
    """
    Create and configure the bot application.
    
    Returns:
        Configured Application instance ready to run
        
    Raises:
        ValueError: If TELEGRAM_BOT_TOKEN is not set
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set")
        raise ValueError("TELEGRAM_BOT_TOKEN is missing from environment variables")
    
    # Build application
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )
    
    # Set lifecycle hooks
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    # Register handlers
    _register_handlers(application)
    
    return application


# =============================================================================
# Entry Point
# =============================================================================

def run_bot() -> None:
    """
    Run the bot.
    
    Creates the application and starts polling for updates.
    This function blocks until the bot is stopped.
    """
    logger.info("Starting English Learning Bot...")
    
    try:
        application = create_application()
        
        # Start polling with all update types enabled
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Ignore updates that arrived while bot was offline
        )
        
    except Exception as e:
        logger.critical(f"Fatal error starting bot: {e}")
        raise


if __name__ == "__main__":
    run_bot()
