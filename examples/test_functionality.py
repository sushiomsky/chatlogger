"""Test script to verify the application can start and database is working."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import ChatDatabase
from datetime import datetime, timezone


def test_database():
    """Test database operations."""
    print("Testing database operations...")
    
    # Use a test database
    db_path = 'test_chat.db'
    
    # Clean up if exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    with ChatDatabase(db_path) as db:
        print("✓ Database created successfully")
        
        # Insert test messages
        db.insert_message(
            username="test_user_1",
            message="Hello from the chat logger!",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        db.insert_message(
            username="test_user_2",
            message="This is a test message",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        print("✓ Test messages inserted")
        
        # Query messages
        count = db.get_message_count()
        print(f"✓ Total messages: {count}")
        
        messages = db.get_messages(limit=10)
        print(f"✓ Retrieved {len(messages)} messages")
        
        for msg in messages:
            print(f"  [{msg['timestamp']}] {msg['username']}: {msg['message']}")
    
    # Clean up test database
    os.remove(db_path)
    print("\n✅ All database tests passed!")


if __name__ == '__main__':
    test_database()
