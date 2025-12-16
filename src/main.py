"""Main application for DuckDice chat logger."""

import argparse
import logging
import signal
import sys
from pathlib import Path

from .database import ChatDatabase
from .chat_client import DuckDiceChatClient


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('chat_logger.log')
    ]
)

logger = logging.getLogger(__name__)


class ChatLogger:
    """Main chat logger application."""
    
    def __init__(self, db_path: str = "chat_logs.db"):
        """Initialize the chat logger.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db = None
        self.client = None
        self.running = False
        
    def on_chat_message(self, message_dict: dict):
        """Handle incoming chat messages.
        
        Args:
            message_dict: Dictionary containing message data
        """
        try:
            if self.db:
                message_id = self.db.insert_message(
                    username=message_dict['username'],
                    message=message_dict['message'],
                    timestamp=message_dict.get('timestamp'),
                    user_id=message_dict.get('user_id'),
                    message_id=message_dict.get('message_id')
                )
                logger.info(f"Saved message #{message_id} from {message_dict['username']}")
        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)
            
    def start(self):
        """Start the chat logger."""
        logger.info("Starting DuckDice Chat Logger")
        
        # Initialize database
        self.db = ChatDatabase(self.db_path)
        self.db.connect()
        logger.info(f"Database initialized at {self.db_path}")
        logger.info(f"Total messages in database: {self.db.get_message_count()}")
        
        # Initialize chat client
        self.client = DuckDiceChatClient(on_message_callback=self.on_chat_message)
        self.client.connect()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        logger.info("Chat logger started. Press Ctrl+C to stop.")
        
        try:
            self.client.run_forever()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the chat logger."""
        if not self.running:
            return
            
        logger.info("Stopping chat logger...")
        self.running = False
        
        if self.client:
            self.client.stop()
            
        if self.db:
            self.db.close()
            
        logger.info("Chat logger stopped")
        
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='DuckDice Chat Logger - Logs public chat to SQLite database'
    )
    parser.add_argument(
        '--db',
        type=str,
        default='chat_logs.db',
        help='Path to SQLite database file (default: chat_logs.db)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    logger = ChatLogger(db_path=args.db)
    logger.start()


if __name__ == '__main__':
    main()
