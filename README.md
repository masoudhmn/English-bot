# English Learning Telegram Bot

A comprehensive Telegram bot for learning English vocabulary using the **Leitner Study Method** - a scientifically proven spaced repetition system.

## 🌟 Features

### 1. **Leitner Study Method**
- Implements proper spaced repetition algorithm
- 7 boxes with increasing review intervals (1, 2, 4, 7, 14, 30, 60 days)
- Adaptive scheduling based on difficulty rating (easy, normal, hard)
- Automatic progression through boxes based on performance

### 2. **Word Management**
- Import words from Excel files (.xlsx)
- Duplicate detection to avoid redundant entries
- Edit words, definitions, examples, and translations
- Track who added and edited each word
- Complete audit trail through edit history

### 3. **User-Friendly Interface**
- Beautiful, intuitive Telegram keyboard menus
- Interactive learning sessions with inline buttons
- Progress tracking and statistics
- Customizable daily word limits

### 4. **Daily Reminders**
- Automatic daily notifications
- Customizable reminder times
- Opt-in/opt-out functionality

### 5. **Progress Analytics**
- Track total words learned
- Monitor mastered words
- View accuracy statistics
- See distribution across Leitner boxes

## 📋 Requirements

- Python 3.12+
- PostgreSQL database
- Telegram Bot Token (from @BotFather)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/masoudhmn/English-bot.git
```

### 2. Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL Database

Create a PostgreSQL database:
```sql
CREATE DATABASE english_bot;
```

### 4. Configure Environment Variables

Copy the example environment file:
```bash
copy .env.example .env
```

Edit `.env` and add your configuration:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/english_bot

# Application Settings
ADMIN_USER_IDS=123456789
TIMEZONE=Asia/Tehran
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

Or create initial migration:
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 6. Run the Bot

```bash
python main.py
```

Or using uv:
```bash
uv run python main.py
```

## 📁 Project Structure

```
05-English_bot/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── bot.py                # Main bot application
│   ├── config.py             # Configuration settings
│   ├── database.py           # Database session management
│   ├── models.py             # SQLAlchemy database models
│   ├── leitner.py            # Leitner algorithm implementation
│   ├── excel_handler.py      # Excel file processing
│   ├── handlers.py           # Telegram bot handlers
│   ├── keyboards.py          # Telegram keyboard layouts
│   └── scheduler.py          # Daily reminder scheduler
├── alembic/                  # Database migrations
│   ├── versions/             # Migration files
│   ├── env.py                # Alembic environment
│   └── script.py.mako        # Migration template
├── alembic.ini               # Alembic configuration
├── main.py                   # Application entry point
├── pyproject.toml            # Project dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 📊 Database Schema

### Tables

1. **users** - Store user information and preferences
   - User ID (Telegram ID)
   - Username, first name, last name
   - Daily word limit
   - Reminder settings
   - Activity tracking

2. **words** - Store English vocabulary
   - Word text
   - Definition
   - Example sentence
   - Translation
   - Added by (user tracking)
   - Timestamps

3. **user_word_progress** - Track learning progress (Leitner system)
   - User-word relationship
   - Current Leitner box (1-7)
   - Difficulty rating
   - Review statistics
   - Next review date

4. **study_sessions** - Track learning sessions
   - Session timing
   - Words reviewed
   - Accuracy statistics
   - New words encountered

5. **word_edit_history** - Audit trail for word edits
   - Word ID
   - Edited by (user)
   - Field changed
   - Old and new values
   - Timestamp

## 📖 Excel File Format

To import words, create an Excel file (.xlsx) with these columns:

### Required Columns:
- **word**: The English word
- **definition**: Word definition

### Optional Columns:
- **example**: Example sentence
- **translation**: Translation (e.g., Persian)

### Sample Excel:

| word        | definition                                    | example                                  | translation      |
|-------------|-----------------------------------------------|------------------------------------------|------------------|
| serendipity | The occurrence of events by chance in a happy way | Finding that old photo was pure serendipity | اتفاق خوش‌شانسانه |
| ephemeral   | Lasting for a very short time                 | The ephemeral beauty of cherry blossoms  | زودگذر، گذرا      |
| eloquent    | Fluent or persuasive in speaking or writing   | She gave an eloquent speech              | شیوا، گویا        |

## 🎮 Bot Commands

- `/start` - Start the bot and set up your account
- `/sample` - Get a sample Excel template
- `/cancel` - Cancel current operation

## 🎯 How to Use

### First Time Setup
1. Start the bot with `/start`
2. Set your daily word limit (recommended: 10-20 words)
3. The main menu will appear

### Adding Words
1. Click **"➕ Add Words"**
2. Upload an Excel file with your vocabulary
3. Bot will confirm how many words were added and show duplicates

### Learning Session
1. Click **"📚 Start Learning"**
2. Bot shows you a word and asks if you know it
3. Click "I Know" or "I Don't Know"
4. Bot shows the definition, example, and translation
5. Rate the difficulty (Easy, Normal, Hard)
6. Continue to the next word

### Viewing Progress
1. Click **"📊 My Progress"**
2. See your statistics:
   - Total words learned
   - Mastered words
   - Words due for review
   - Accuracy percentage
   - Distribution across Leitner boxes

### Editing Words
1. Click **"✏️ Edit Word"**
2. Enter the word you want to edit
3. Select which field to edit
4. Enter the new value

### Settings
1. Click **"⚙️ Settings"**
2. Customize:
   - Daily word limit
   - Enable/disable reminders
   - Set reminder time

## 🔄 Leitner System Explained

The bot uses a 7-box Leitner system:

- **Box 1**: Review after 1 day (new/difficult words)
- **Box 2**: Review after 2 days
- **Box 3**: Review after 4 days
- **Box 4**: Review after 7 days
- **Box 5**: Review after 14 days
- **Box 6**: Review after 30 days
- **Box 7**: Review after 60 days (mastered)

**How it works:**
- If you know a word correctly, it moves to the next box (longer interval)
- If you don't know it, it goes back to Box 1 (review tomorrow)
- Difficulty rating adjusts the schedule:
  - **Easy**: +50% longer interval
  - **Normal**: Standard interval
  - **Hard**: -30% shorter interval

## 🔒 Security & Privacy

- All data is stored securely in PostgreSQL
- User passwords are never stored or required
- Only Telegram authentication is used
- Edit history maintains full audit trail

## 🛠️ Development

### Running Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

### Adding New Features

1. Update models in `src/models.py`
2. Create migration with `alembic revision --autogenerate`
3. Add handlers in `src/handlers.py`
4. Update keyboards in `src/keyboards.py`
5. Test thoroughly before deployment

## 📝 TODO / Future Enhancements

- [ ] Add pronunciation support (audio/phonetic)
- [ ] Support multiple languages
- [ ] Add word categories/tags
- [ ] Implement word search functionality
- [ ] Export user progress to Excel
- [ ] Add gamification (streaks, achievements)
- [ ] Support for phrases/idioms
- [ ] Quiz mode with multiple choices
- [ ] API for third-party integrations

## 🐛 Troubleshooting

### Database Connection Issues
```
Error: could not connect to server
```
**Solution**: Ensure PostgreSQL is running and DATABASE_URL is correct

### Bot Not Responding
```
Error: Unauthorized
```
**Solution**: Check TELEGRAM_BOT_TOKEN in .env file

### Import Errors
```
ModuleNotFoundError: No module named 'src'
```
**Solution**: Run the bot from the project root directory

### Alembic Migration Issues
```
Error: Can't locate revision identified by 'xxxxx'
```
**Solution**: 
```bash
alembic stamp head
alembic revision --autogenerate -m "Reset migration"
```

## 📄 License

This project is created for educational purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please create an issue in the repository.

---

**Made with ❤️ for English learners**
