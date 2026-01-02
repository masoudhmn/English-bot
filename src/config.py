"""Configuration module for the application"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/english_bot")

# Application Settings
ADMIN_USER_IDS = [int(uid) for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid]
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# Leitner System Configuration
LEITNER_BOXES = {
    1: 1,      # Review after 1 day
    2: 2,      # Review after 2 days
    3: 4,      # Review after 4 days
    4: 7,      # Review after 7 days
    5: 14,     # Review after 14 days
    6: 30,     # Review after 30 days
    7: 60,     # Review after 60 days (mastered)
}

# Daily reminder time (hour, minute)
DAILY_REMINDER_TIME = (9, 0)  # 9:00 AM

# Excel file configuration
EXCEL_COLUMNS = {
    "word": "word",
    "definition": "definition",
    "example": "example",
    "translation": "translation",
}
