"""WebSocket client for connecting to DuckDice chat."""

import json
import logging
import time
from typing import Callable, Optional
import websocket
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class DuckDiceChatClient:
    """WebSocket client for DuckDice public chat."""
    
    # Based on reverse engineering and common patterns for Socket.IO/WebSocket
    WEBSOCKET_URL = "wss://duckdice.io/socket.io/?EIO=4&transport=websocket"
    
    def __init__(self, on_message_callback: Callable[[dict], None]):
        """Initialize the chat client.
        
        Args:
            on_message_callback: Callback function to handle received messages
        """
        self.ws = None
        self.on_message_callback = on_message_callback
        self.running = False
        self.ping_interval = 25  # Send ping every 25 seconds
        self.last_ping = 0
        
    def connect(self):
        """Connect to the DuckDice WebSocket."""
        logger.info(f"Connecting to {self.WEBSOCKET_URL}")
        
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.WEBSOCKET_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
    def _on_open(self, ws):
        """Handle WebSocket connection opened."""
        logger.info("WebSocket connection established")
        self.running = True
        self.last_ping = time.time()
        
        # Socket.IO initialization - send a hello message
        # Engine.IO v4 protocol
        ws.send("40")  # Socket.IO connect packet
        
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages.
        
        Args:
            ws: WebSocket instance
            message: Raw message string
        """
        try:
            # Parse Socket.IO protocol messages
            # Format: <packet_type><optional_namespace>,<optional_json>
            
            if message.startswith("0"):
                # Engine.IO open packet
                logger.debug(f"Engine.IO open: {message}")
                config = json.loads(message[1:])
                self.ping_interval = config.get('pingInterval', 25000) / 1000
                
            elif message.startswith("2"):
                # Ping packet - respond with pong
                ws.send("3")
                logger.debug("Received ping, sent pong")
                
            elif message.startswith("40"):
                # Socket.IO connected
                logger.info("Socket.IO connected")
                
            elif message.startswith("42"):
                # Socket.IO event packet
                data = json.loads(message[2:])
                self._handle_event(data)
                
            elif message.startswith("3"):
                # Pong packet
                logger.debug("Received pong")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            
    def _handle_event(self, data):
        """Handle Socket.IO events.
        
        Args:
            data: Parsed event data (list format: [event_name, event_data])
        """
        if not isinstance(data, list) or len(data) < 1:
            return
            
        event_name = data[0]
        
        # Chat message events (common patterns)
        if event_name in ['chat', 'message', 'chat_message', 'new_message']:
            if len(data) > 1:
                event_data = data[1]
                self._process_chat_message(event_data)
                
    def _process_chat_message(self, event_data):
        """Process a chat message event.
        
        Args:
            event_data: Message data dictionary
        """
        try:
            # Extract message details based on common patterns
            message_dict = {
                'username': event_data.get('username') or event_data.get('user') or event_data.get('name') or 'Unknown',
                'message': event_data.get('message') or event_data.get('text') or event_data.get('content') or '',
                'timestamp': event_data.get('timestamp') or event_data.get('time') or datetime.now(timezone.utc).isoformat(),
                'user_id': event_data.get('user_id') or event_data.get('userId') or event_data.get('uid'),
                'message_id': event_data.get('message_id') or event_data.get('messageId') or event_data.get('id')
            }
            
            logger.info(f"Chat message from {message_dict['username']}: {message_dict['message']}")
            self.on_message_callback(message_dict)
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}", exc_info=True)
            
    def _on_error(self, ws, error):
        """Handle WebSocket errors.
        
        Args:
            ws: WebSocket instance
            error: Error object
        """
        logger.error(f"WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closed.
        
        Args:
            ws: WebSocket instance
            close_status_code: Close status code
            close_msg: Close message
        """
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.running = False
        
    def run_forever(self):
        """Run the WebSocket client forever (blocking)."""
        if self.ws:
            self.ws.run_forever(ping_interval=self.ping_interval)
            
    def stop(self):
        """Stop the WebSocket client."""
        self.running = False
        if self.ws:
            self.ws.close()
