# DuckDice Chat Logger

A Python application that connects to the DuckDice.io public webchat and logs all messages to a local SQLite database.

## Features

- Real-time WebSocket connection to DuckDice.io public chat
- Automatic logging of all chat messages to SQLite database
- Indexed database for efficient querying
- Graceful shutdown handling
- Comprehensive test coverage
- Easy to use CLI interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sushiomsky/chatlogger.git
cd chatlogger
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install in development mode:
```bash
pip install -e ".[dev]"
```

## Usage

### Basic Usage

Run the chat logger with default settings:
```bash
python -m src.main
```

### Custom Database Path

Specify a custom database file:
```bash
python -m src.main --db /path/to/database.db
```

### Verbose Logging

Enable verbose logging for debugging:
```bash
python -m src.main --verbose
```

### Stop the Logger

Press `Ctrl+C` to gracefully stop the logger.

## Database Schema

The application creates a SQLite database with the following schema:

```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    username TEXT NOT NULL,
    message TEXT NOT NULL,
    user_id TEXT,
    message_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Indexes are created on `timestamp` and `username` columns for efficient querying.

## Querying the Database

You can query the database using any SQLite client or Python:

```python
from src.database import ChatDatabase

with ChatDatabase('chat_logs.db') as db:
    # Get last 100 messages
    messages = db.get_messages(limit=100)
    
    # Get messages from specific user
    user_messages = db.get_messages_by_user('username')
    
    # Get total message count
    count = db.get_message_count()
```

## Testing

Run the test suite:
```bash
pytest
```

Run tests with coverage report:
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

## Architecture

The application consists of three main components:

1. **Database Module (`src/database.py`)**: Handles SQLite database operations
   - Creates and manages database schema
   - Provides methods for inserting and querying messages
   - Implements context manager for safe resource handling

2. **Chat Client (`src/chat_client.py`)**: WebSocket client for DuckDice.io
   - Connects to DuckDice.io WebSocket endpoint
   - Handles Socket.IO protocol messages
   - Parses chat events and extracts message data
   - Implements automatic ping/pong for connection keep-alive

3. **Main Application (`src/main.py`)**: Orchestrates the components
   - Initializes database and chat client
   - Handles incoming messages and saves to database
   - Manages graceful shutdown on signals
   - Provides CLI interface

## WebSocket Protocol

The application uses the Socket.IO protocol (Engine.IO v4) to connect to DuckDice.io:

- **Connection URL**: `wss://duckdice.io/socket.io/?EIO=4&transport=websocket`
- **Protocol**: Socket.IO with Engine.IO v4 transport
- **Message Format**: JSON-encoded events
- **Keep-alive**: Automatic ping/pong every 25 seconds

## Troubleshooting

### Connection Issues

If you encounter connection issues:
1. Check your internet connection
2. Verify that DuckDice.io is accessible
3. Enable verbose logging with `--verbose` flag
4. Check the `chat_logger.log` file for detailed error messages

### Database Locked

If you get "database is locked" errors:
- Make sure only one instance of the logger is running
- Check file permissions on the database file
- Ensure the database file is not opened in another application

## Development

### Project Structure

```
chatlogger/
├── src/
│   ├── __init__.py
│   ├── main.py          # Main application
│   ├── database.py      # Database operations
│   └── chat_client.py   # WebSocket client
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   └── test_chat_client.py
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_database.py

# Run with coverage
pytest --cov=src --cov-report=html
```

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
