# Quick Start Guide

Get your English Learning Bot up and running in 5 minutes!

## Prerequisites

✅ Python 3.12+ installed  
✅ PostgreSQL installed and running  
✅ Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

## Step-by-Step Setup

### 1️⃣ Install Dependencies

```bash
# Using uv (recommended)
uv sync

# OR using pip
pip install -r requirements.txt
```

### 2️⃣ Create PostgreSQL Database

```bash
# Open PostgreSQL command line
psql -U postgres

# Create database
CREATE DATABASE english_bot;

# Exit
\q
```

### 3️⃣ Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env and add your credentials
# Required: TELEGRAM_BOT_TOKEN, DATABASE_URL
```

**Example .env:**
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=postgresql://postgres:password@localhost:5432/english_bot
ADMIN_USER_IDS=
TIMEZONE=Asia/Tehran
```

### 4️⃣ Initialize Database

```bash
# Run database setup
python setup_db.py

# OR using alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 5️⃣ Start the Bot

```bash
# Run the bot
python main.py

# OR using uv
uv run python main.py
```

You should see:
```
INFO - Starting English Learning Bot...
INFO - Initializing database...
INFO - Database initialized!
INFO - Setting up daily reminders...
INFO - Scheduler setup complete!
```

## 🎉 Test Your Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start`
4. Follow the setup wizard!

## 📝 First Steps

### Add Your First Words

1. Download the sample template:
   - Click **"📖 Sample Excel"** in bot
   - OR run `/sample` command

2. Fill in your words in the Excel file:
   - Column A: word
   - Column B: definition
   - Column C: example (optional)
   - Column D: translation (optional)

3. Upload the file:
   - Click **"➕ Add Words"**
   - Send the Excel file

### Start Learning

1. Click **"📚 Start Learning"**
2. Answer if you know each word
3. Rate the difficulty
4. Review your progress!

## 🔧 Common Issues

### Issue: "ModuleNotFoundError: No module named 'telegram'"

**Solution:**
```bash
pip install python-telegram-bot[job-queue]
```

### Issue: "could not connect to server"

**Solutions:**
1. Check if PostgreSQL is running:
   ```bash
   # Windows
   net start postgresql-x64-14
   
   # Linux/Mac
   sudo systemctl start postgresql
   ```

2. Verify DATABASE_URL in .env matches your setup

### Issue: "Error: Unauthorized"

**Solution:**
- Get a new token from @BotFather
- Update TELEGRAM_BOT_TOKEN in .env
- Restart the bot

### Issue: Import paths not working

**Solution:**
Make sure you're running from the project root:
```bash
cd "c:\Users\Masoud\Desktop\my long term project\05-English_bot"
python main.py
```

## 📚 Next Steps

✨ Customize your daily word limit  
✨ Set up daily reminders  
✨ Import your word lists  
✨ Start learning consistently!  

## 🆘 Need Help?

- Read the full [README.md](README.md)
- Check the database schema in `src/models.py`
- Review bot handlers in `src/handlers.py`

---

**Happy Learning! 🚀**
