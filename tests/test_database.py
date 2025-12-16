"""Tests for the database module."""

import os
import tempfile
import pytest
from datetime import datetime

from src.database import ChatDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = ChatDatabase(path)
    db.connect()
    
    yield db
    
    db.close()
    os.unlink(path)


def test_database_creation(temp_db):
    """Test database and table creation."""
    assert temp_db.conn is not None
    assert temp_db.cursor is not None
    
    # Check that tables exist
    temp_db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'"
    )
    assert temp_db.cursor.fetchone() is not None


def test_insert_message(temp_db):
    """Test inserting a chat message."""
    message_id = temp_db.insert_message(
        username="test_user",
        message="Hello, world!",
        timestamp="2024-01-01T12:00:00",
        user_id="user123",
        message_id="msg456"
    )
    
    assert message_id > 0
    assert temp_db.get_message_count() == 1


def test_insert_multiple_messages(temp_db):
    """Test inserting multiple chat messages."""
    for i in range(5):
        temp_db.insert_message(
            username=f"user_{i}",
            message=f"Message {i}",
            timestamp=f"2024-01-01T12:00:{i:02d}"
        )
    
    assert temp_db.get_message_count() == 5


def test_get_messages(temp_db):
    """Test retrieving messages."""
    # Insert test messages
    temp_db.insert_message(
        username="alice",
        message="First message",
        timestamp="2024-01-01T12:00:00"
    )
    temp_db.insert_message(
        username="bob",
        message="Second message",
        timestamp="2024-01-01T12:01:00"
    )
    
    messages = temp_db.get_messages(limit=10)
    
    assert len(messages) == 2
    # Messages should be in reverse chronological order
    assert messages[0]['username'] == 'bob'
    assert messages[1]['username'] == 'alice'


def test_get_messages_pagination(temp_db):
    """Test message retrieval with pagination."""
    # Insert 10 messages
    for i in range(10):
        temp_db.insert_message(
            username=f"user_{i}",
            message=f"Message {i}",
            timestamp=f"2024-01-01T12:00:{i:02d}"
        )
    
    # Get first page
    page1 = temp_db.get_messages(limit=5, offset=0)
    assert len(page1) == 5
    
    # Get second page
    page2 = temp_db.get_messages(limit=5, offset=5)
    assert len(page2) == 5
    
    # Ensure no overlap
    page1_ids = [msg['id'] for msg in page1]
    page2_ids = [msg['id'] for msg in page2]
    assert len(set(page1_ids) & set(page2_ids)) == 0


def test_get_messages_by_user(temp_db):
    """Test retrieving messages by specific user."""
    # Insert messages from different users
    temp_db.insert_message(username="alice", message="Message 1")
    temp_db.insert_message(username="bob", message="Message 2")
    temp_db.insert_message(username="alice", message="Message 3")
    temp_db.insert_message(username="charlie", message="Message 4")
    temp_db.insert_message(username="alice", message="Message 5")
    
    alice_messages = temp_db.get_messages_by_user("alice")
    
    assert len(alice_messages) == 3
    for msg in alice_messages:
        assert msg['username'] == 'alice'


def test_message_count(temp_db):
    """Test message count functionality."""
    assert temp_db.get_message_count() == 0
    
    temp_db.insert_message(username="user1", message="Test")
    assert temp_db.get_message_count() == 1
    
    temp_db.insert_message(username="user2", message="Test 2")
    assert temp_db.get_message_count() == 2


def test_auto_timestamp(temp_db):
    """Test automatic timestamp generation."""
    message_id = temp_db.insert_message(
        username="test_user",
        message="Test message"
    )
    
    messages = temp_db.get_messages()
    assert len(messages) == 1
    assert messages[0]['timestamp'] is not None


def test_context_manager():
    """Test database context manager."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        with ChatDatabase(path) as db:
            db.insert_message(username="test", message="test")
            count = db.get_message_count()
            assert count == 1
    finally:
        os.unlink(path)


def test_message_fields(temp_db):
    """Test that all message fields are stored and retrieved correctly."""
    temp_db.insert_message(
        username="testuser",
        message="Test message content",
        timestamp="2024-01-01T12:00:00",
        user_id="uid123",
        message_id="msgid456"
    )
    
    messages = temp_db.get_messages()
    assert len(messages) == 1
    
    msg = messages[0]
    assert msg['username'] == 'testuser'
    assert msg['message'] == 'Test message content'
    assert msg['timestamp'] == '2024-01-01T12:00:00'
    assert msg['user_id'] == 'uid123'
    assert msg['message_id'] == 'msgid456'
    assert msg['created_at'] is not None


def test_empty_database(temp_db):
    """Test operations on empty database."""
    assert temp_db.get_message_count() == 0
    assert temp_db.get_messages() == []
    assert temp_db.get_messages_by_user("nonexistent") == []
