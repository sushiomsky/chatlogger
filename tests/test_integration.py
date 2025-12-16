"""Integration tests for the complete application."""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.main import ChatLogger
from src.database import ChatDatabase


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_chat_logger_initialization(temp_db_path):
    """Test ChatLogger initialization."""
    logger = ChatLogger(db_path=temp_db_path)
    
    assert logger.db_path == temp_db_path
    assert logger.db is None
    assert logger.client is None
    assert logger.running is False


def test_on_chat_message_saves_to_database(temp_db_path):
    """Test that incoming chat messages are saved to database."""
    logger = ChatLogger(db_path=temp_db_path)
    logger.db = ChatDatabase(temp_db_path)
    logger.db.connect()
    
    # Simulate a chat message
    message_dict = {
        'username': 'test_user',
        'message': 'Test message',
        'timestamp': '2024-01-01T12:00:00',
        'user_id': 'user123',
        'message_id': 'msg456'
    }
    
    logger.on_chat_message(message_dict)
    
    # Verify it was saved
    messages = logger.db.get_messages()
    assert len(messages) == 1
    assert messages[0]['username'] == 'test_user'
    assert messages[0]['message'] == 'Test message'
    
    logger.db.close()


def test_on_chat_message_handles_errors(temp_db_path):
    """Test that errors during message saving are handled gracefully."""
    logger = ChatLogger(db_path=temp_db_path)
    # Don't initialize database - this will cause an error
    
    message_dict = {
        'username': 'test_user',
        'message': 'Test message'
    }
    
    # Should not crash when database is not initialized
    logger.on_chat_message(message_dict)
    
    # If we get here without exception, test passes
    assert True


def test_stop_cleans_up_resources(temp_db_path):
    """Test that stop() properly cleans up resources."""
    logger = ChatLogger(db_path=temp_db_path)
    logger.db = ChatDatabase(temp_db_path)
    logger.db.connect()
    logger.client = Mock()
    logger.running = True
    
    logger.stop()
    
    assert logger.running is False
    logger.client.stop.assert_called_once()
    # Database connection should be closed


def test_multiple_messages_flow(temp_db_path):
    """Test handling multiple messages in sequence."""
    logger = ChatLogger(db_path=temp_db_path)
    logger.db = ChatDatabase(temp_db_path)
    logger.db.connect()
    
    # Simulate multiple messages
    messages = [
        {'username': 'user1', 'message': 'Hello', 'timestamp': '2024-01-01T12:00:00'},
        {'username': 'user2', 'message': 'Hi there', 'timestamp': '2024-01-01T12:00:01'},
        {'username': 'user1', 'message': 'How are you?', 'timestamp': '2024-01-01T12:00:02'},
    ]
    
    for msg in messages:
        logger.on_chat_message(msg)
    
    # Verify all messages were saved
    saved_messages = logger.db.get_messages()
    assert len(saved_messages) == 3
    
    # Verify they're in reverse chronological order
    assert saved_messages[0]['message'] == 'How are you?'
    assert saved_messages[1]['message'] == 'Hi there'
    assert saved_messages[2]['message'] == 'Hello'
    
    logger.db.close()


def test_user_specific_queries(temp_db_path):
    """Test querying messages by specific user."""
    logger = ChatLogger(db_path=temp_db_path)
    logger.db = ChatDatabase(temp_db_path)
    logger.db.connect()
    
    # Simulate messages from different users
    messages = [
        {'username': 'alice', 'message': 'Message 1', 'timestamp': '2024-01-01T12:00:00'},
        {'username': 'bob', 'message': 'Message 2', 'timestamp': '2024-01-01T12:00:01'},
        {'username': 'alice', 'message': 'Message 3', 'timestamp': '2024-01-01T12:00:02'},
        {'username': 'bob', 'message': 'Message 4', 'timestamp': '2024-01-01T12:00:03'},
        {'username': 'alice', 'message': 'Message 5', 'timestamp': '2024-01-01T12:00:04'},
    ]
    
    for msg in messages:
        logger.on_chat_message(msg)
    
    # Query alice's messages
    alice_messages = logger.db.get_messages_by_user('alice')
    assert len(alice_messages) == 3
    assert all(msg['username'] == 'alice' for msg in alice_messages)
    
    # Query bob's messages
    bob_messages = logger.db.get_messages_by_user('bob')
    assert len(bob_messages) == 2
    assert all(msg['username'] == 'bob' for msg in bob_messages)
    
    logger.db.close()
