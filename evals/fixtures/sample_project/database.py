"""SQLite database layer for the User Management API.

Provides Database class connecting to local SQLite database and helper
functions to perform CRUD actions on the users table.
"""

import sqlite3
import os
import datetime
from models import User, UserCreate

DB_PATH = "users.db"

class Database:
    """Handles connection and CRUD operations on the SQLite database."""
    
    def __init__(self) -> None:
        """Initialize connection object and database file path."""
        self.conn: Optional[sqlite3.Connection] = None
        self.db_path: str = DB_PATH
        
    def connect(self) -> None:
        """Establish connection to SQLite and initialize database tables."""
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
        
    def disconnect(self) -> None:
        """Close connection to SQLite if active."""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def _create_tables(self) -> None:
        """Create users table if not exists."""
        if not self.conn:
            raise RuntimeError("Database connection not established. Call connect() first.")
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        self.conn.commit()
        
    def get_all_users(self) -> list[User]:
        """Retrieve all users from the database."""
        if not self.conn:
            raise RuntimeError("Database connection not established.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, email, created_at, is_active, password FROM users")
        rows = cursor.fetchall()
        
        users_list = []
        for row in rows:
            # Map SQLite columns to User Pydantic model
            user = User(
                id=row[0],
                name=row[1],
                email=row[2],
                created_at=row[3],
                is_active=bool(row[4])
            )
            # Attach password dynamically to keep model consistent
            user.password = row[5]
            users_list.append(user)
        return users_list
        
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Fetch a single user from database by ID."""
        if not self.conn:
            raise RuntimeError("Database connection not established.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, email, created_at, is_active, password FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            user = User(
                id=row[0],
                name=row[1],
                email=row[2],
                created_at=row[3],
                is_active=bool(row[4])
            )
            user.password = row[5]
            return user
        return None
        
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Fetch a single user from database by email."""
        if not self.conn:
            raise RuntimeError("Database connection not established.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, email, created_at, is_active, password FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            user = User(
                id=row[0],
                name=row[1],
                email=row[2],
                created_at=row[3],
                is_active=bool(row[4])
            )
            user.password = row[5]
            return user
        return None
        
    def insert_user(self, user_data: UserCreate) -> User:
        """Insert new user record into database and return corresponding User object."""
        if not self.conn:
            raise RuntimeError("Database connection not established.")
        created_at_str = datetime.datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password, created_at, is_active) VALUES (?, ?, ?, ?, ?)",
            (user_data.name, user_data.email, user_data.password, created_at_str, 1)
        )
        self.conn.commit()
        user_id = cursor.lastrowid
        
        user = User(
            id=user_id,
            name=user_data.name,
            email=user_data.email,
            created_at=created_at_str,
            is_active=True
        )
        user.password = user_data.password
        return user

# Module-level Database singleton
_db_instance: Optional[Database] = None

def get_db() -> Database:
    """Retrieve or initialize the global Database singleton instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
