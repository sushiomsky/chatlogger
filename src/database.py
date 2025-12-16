"""Database module for storing chat messages."""

import sqlite3
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional


class ChatDatabase:
    """Manages SQLite database for chat messages."""
    
    def __init__(self, db_path: str = "chat_logs.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to the database and create tables if needed."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
        
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id TEXT,
                message_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON chat_messages(timestamp)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_username 
            ON chat_messages(username)
        ''')
        
        self.conn.commit()
        
    def insert_message(self, username: str, message: str, 
                      timestamp: Optional[str] = None,
                      user_id: Optional[str] = None,
                      message_id: Optional[str] = None) -> int:
        """Insert a chat message into the database.
        
        Args:
            username: Username of the message sender
            message: Content of the message
            timestamp: Timestamp of the message (ISO format)
            user_id: User ID if available
            message_id: Message ID if available
            
        Returns:
            The ID of the inserted message
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
            
        self.cursor.execute('''
            INSERT INTO chat_messages 
            (timestamp, username, message, user_id, message_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, username, message, user_id, message_id))
        
        self.conn.commit()
        return self.cursor.lastrowid
        
    def get_messages(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Retrieve chat messages from the database.
        
        Args:
            limit: Maximum number of messages to retrieve
            offset: Number of messages to skip
            
        Returns:
            List of message dictionaries
        """
        self.cursor.execute('''
            SELECT id, timestamp, username, message, user_id, message_id, created_at
            FROM chat_messages
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = self.cursor.fetchall()
        messages = []
        for row in rows:
            messages.append({
                'id': row[0],
                'timestamp': row[1],
                'username': row[2],
                'message': row[3],
                'user_id': row[4],
                'message_id': row[5],
                'created_at': row[6]
            })
        return messages
        
    def get_messages_by_user(self, username: str, limit: int = 100) -> List[Dict]:
        """Retrieve chat messages from a specific user.
        
        Args:
            username: Username to filter by
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        self.cursor.execute('''
            SELECT id, timestamp, username, message, user_id, message_id, created_at
            FROM chat_messages
            WHERE username = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (username, limit))
        
        rows = self.cursor.fetchall()
        messages = []
        for row in rows:
            messages.append({
                'id': row[0],
                'timestamp': row[1],
                'username': row[2],
                'message': row[3],
                'user_id': row[4],
                'message_id': row[5],
                'created_at': row[6]
            })
        return messages
        
    def get_message_count(self) -> int:
        """Get total count of messages in database.
        
        Returns:
            Total number of messages
        """
        self.cursor.execute('SELECT COUNT(*) FROM chat_messages')
        return self.cursor.fetchone()[0]
        
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
