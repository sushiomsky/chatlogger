"""Tests for the chat client module."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.chat_client import DuckDiceChatClient


@pytest.fixture
def callback_mock():
    """Create a mock callback function."""
    return Mock()


@pytest.fixture
def client(callback_mock):
    """Create a chat client instance with mock callback."""
    return DuckDiceChatClient(on_message_callback=callback_mock)


def test_client_initialization(client, callback_mock):
    """Test client initialization."""
    assert client.on_message_callback == callback_mock
    assert client.ws is None
    assert client.running is False


def test_parse_engine_io_open(client):
    """Test parsing Engine.IO open packet."""
    ws_mock = Mock()
    
    open_packet = '0{"sid":"test123","upgrades":[],"pingInterval":25000,"pingTimeout":20000}'
    client._on_message(ws_mock, open_packet)
    
    # Should update ping interval
    assert client.ping_interval == 25.0


def test_parse_ping_pong(client):
    """Test ping/pong handling."""
    ws_mock = Mock()
    
    # Receive ping
    client._on_message(ws_mock, "2")
    
    # Should send pong
    ws_mock.send.assert_called_once_with("3")


def test_socket_io_connected(client):
    """Test Socket.IO connection packet."""
    ws_mock = Mock()
    
    # Socket.IO connected packet
    client._on_message(ws_mock, "40")
    
    # Should not raise any errors
    assert True


def test_chat_message_parsing(client, callback_mock):
    """Test parsing chat message events."""
    ws_mock = Mock()
    
    # Socket.IO event with chat message
    chat_event = [
        "chat",
        {
            "username": "testuser",
            "message": "Hello, world!",
            "timestamp": "2024-01-01T12:00:00",
            "user_id": "user123",
            "message_id": "msg456"
        }
    ]
    
    message_packet = "42" + json.dumps(chat_event)
    client._on_message(ws_mock, message_packet)
    
    # Callback should be called with message data
    callback_mock.assert_called_once()
    call_args = callback_mock.call_args[0][0]
    
    assert call_args['username'] == 'testuser'
    assert call_args['message'] == 'Hello, world!'
    assert call_args['timestamp'] == '2024-01-01T12:00:00'


def test_chat_message_alternative_format(client, callback_mock):
    """Test parsing chat messages with alternative field names."""
    ws_mock = Mock()
    
    # Alternative format with different field names
    chat_event = [
        "message",
        {
            "user": "alice",
            "text": "Test message",
            "time": "2024-01-01T12:00:00"
        }
    ]
    
    message_packet = "42" + json.dumps(chat_event)
    client._on_message(ws_mock, message_packet)
    
    callback_mock.assert_called_once()
    call_args = callback_mock.call_args[0][0]
    
    assert call_args['username'] == 'alice'
    assert call_args['message'] == 'Test message'


def test_chat_message_minimal_data(client, callback_mock):
    """Test parsing chat messages with minimal data."""
    ws_mock = Mock()
    
    # Minimal message format
    chat_event = [
        "new_message",
        {
            "name": "bob",
            "content": "Hi there"
        }
    ]
    
    message_packet = "42" + json.dumps(chat_event)
    client._on_message(ws_mock, message_packet)
    
    callback_mock.assert_called_once()
    call_args = callback_mock.call_args[0][0]
    
    assert call_args['username'] == 'bob'
    assert call_args['message'] == 'Hi there'
    assert call_args['timestamp'] is not None  # Should have auto-generated timestamp


def test_invalid_message_handling(client, callback_mock):
    """Test handling of invalid messages."""
    ws_mock = Mock()
    
    # Invalid JSON
    client._on_message(ws_mock, "42{invalid json}")
    
    # Should not crash, callback should not be called
    callback_mock.assert_not_called()


def test_non_chat_event(client, callback_mock):
    """Test ignoring non-chat events."""
    ws_mock = Mock()
    
    # Non-chat event
    other_event = ["some_other_event", {"data": "value"}]
    message_packet = "42" + json.dumps(other_event)
    
    client._on_message(ws_mock, message_packet)
    
    # Callback should not be called for non-chat events
    callback_mock.assert_not_called()


def test_on_open(client):
    """Test WebSocket open handler."""
    ws_mock = Mock()
    
    client._on_open(ws_mock)
    
    assert client.running is True
    # Should send Socket.IO connect packet
    ws_mock.send.assert_called_once_with("40")


def test_on_close(client):
    """Test WebSocket close handler."""
    ws_mock = Mock()
    client.running = True
    
    client._on_close(ws_mock, 1000, "Normal closure")
    
    assert client.running is False


def test_on_error(client):
    """Test WebSocket error handler."""
    ws_mock = Mock()
    
    # Should not raise exception
    client._on_error(ws_mock, Exception("Test error"))


def test_stop(client):
    """Test stopping the client."""
    client.ws = Mock()
    client.running = True
    
    client.stop()
    
    assert client.running is False
    client.ws.close.assert_called_once()


def test_process_chat_message_missing_fields(client, callback_mock):
    """Test processing chat message with missing optional fields."""
    event_data = {
        "username": "testuser",
        "message": "Test"
    }
    
    client._process_chat_message(event_data)
    
    callback_mock.assert_called_once()
    call_args = callback_mock.call_args[0][0]
    
    assert call_args['username'] == 'testuser'
    assert call_args['message'] == 'Test'
    assert call_args['user_id'] is None
    assert call_args['message_id'] is None
