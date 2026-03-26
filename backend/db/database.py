"""
Async SQLite database connection and initialization
"""
import aiosqlite
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from config import get_settings

# Global database connection
_db_connection: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    """Get the database connection"""
    global _db_connection
    if _db_connection is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_connection


async def init_db():
    """Initialize the database connection and create tables"""
    global _db_connection
    settings = get_settings()
    db_path = Path(settings.database_path)

    _db_connection = await aiosqlite.connect(str(db_path))
    _db_connection.row_factory = aiosqlite.Row

    await _create_tables(_db_connection)


async def close_db():
    """Close the database connection"""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None


@asynccontextmanager
async def get_db_context():
    """Context manager for database operations"""
    db = await get_db()
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise


async def _create_tables(conn: aiosqlite.Connection):
    """Create database tables if they don't exist"""

    # Profiles table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id TEXT PRIMARY KEY,
            serial_number TEXT UNIQUE,
            name TEXT,
            domain_name TEXT,
            group_id TEXT,
            group_name TEXT,
            created_time TEXT,
            last_open_time TEXT,
            ip TEXT,
            ip_country TEXT,
            followers_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            bio TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add bio column if it doesn't exist (migration)
    try:
        await conn.execute('ALTER TABLE profiles ADD COLUMN bio TEXT')
    except Exception:
        pass  # Column already exists

    # Add location column if it doesn't exist (migration)
    try:
        await conn.execute('ALTER TABLE profiles ADD COLUMN location TEXT')
    except Exception:
        pass  # Column already exists

    # Actions table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT,
            action_type TEXT,
            action_name TEXT,
            assigned_count INTEGER DEFAULT 0,
            completed_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (user_id)
        )
    ''')

    # Tasks queue table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            task_data TEXT,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 0,
            batch_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (user_id)
        )
    ''')

    # Selector cache table (for MCP self-healing)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS selector_cache (
            name TEXT PRIMARY KEY,
            selector TEXT NOT NULL,
            last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0
        )
    ''')

    # Session logs table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT,
            session_id TEXT,
            level TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (user_id)
        )
    ''')

    # Daily stats table for tracking action statistics per day
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            profile_id TEXT,
            follows_count INTEGER DEFAULT 0,
            unfollows_count INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            retweets_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            tweets_posted_count INTEGER DEFAULT 0,
            total_actions INTEGER DEFAULT 0,
            successful_actions INTEGER DEFAULT 0,
            failed_actions INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, profile_id)
        )
    ''')

    # Session summaries table for tracking bot sessions
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            profile_id TEXT,
            started_at TIMESTAMP NOT NULL,
            ended_at TIMESTAMP,
            duration_seconds INTEGER,
            total_actions INTEGER DEFAULT 0,
            follows_count INTEGER DEFAULT 0,
            unfollows_count INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            retweets_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            tweets_posted_count INTEGER DEFAULT 0,
            successful_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            errors_json TEXT,
            error_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    ''')

    await conn.commit()


async def execute_query(query: str, params: tuple = ()):
    """Execute a query and return cursor"""
    db = await get_db()
    cursor = await db.execute(query, params)
    return cursor


async def fetch_one(query: str, params: tuple = ()):
    """Fetch one row"""
    cursor = await execute_query(query, params)
    return await cursor.fetchone()


async def fetch_all(query: str, params: tuple = ()):
    """Fetch all rows"""
    cursor = await execute_query(query, params)
    return await cursor.fetchall()


async def execute_and_commit(query: str, params: tuple = ()):
    """Execute a query and commit"""
    db = await get_db()
    cursor = await db.execute(query, params)
    await db.commit()
    return cursor.lastrowid
