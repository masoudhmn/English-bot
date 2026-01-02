"""
Database setup script
Run this to create initial database migration
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import init_db
from src.config import DATABASE_URL


async def setup_database():
    """Initialize database tables"""
    print("=" * 50)
    print("English Learning Bot - Database Setup")
    print("=" * 50)
    print()
    print(f"Database URL: {DATABASE_URL}")
    print()
    
    try:
        print("Creating database tables...")
        await init_db()
        print("✅ Database tables created successfully!")
        print()
        print("Next steps:")
        print("1. Add your bot token to .env file")
        print("2. Run: python main.py")
        print()
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        print()
        print("Please check:")
        print("1. PostgreSQL is running")
        print("2. DATABASE_URL in .env is correct")
        print("3. Database exists (CREATE DATABASE english_bot;)")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_database())
