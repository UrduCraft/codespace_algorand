"""
Silexa WebSocket Manager
Handles WebSocket connections for real-time messaging
"""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time messaging"""
    
    def __init__(self):
        # Store active connections: user_address -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Track user status: user_address -> {"is_online": bool, "last_seen": datetime}
        self.user_status: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_address: str):
        """Accept a new WebSocket connection"""
        try:
            await websocket.accept()
            self.active_connections[user_address] = websocket
            
            # Update user status
            self.user_status[user_address] = {
                "is_online": True,
                "last_seen": datetime.utcnow(),
                "connected_at": datetime.utcnow()
            }
            
            # Notify other users about online status
            await self._broadcast_user_status(user_address, True)
            
            logger.info(f"WebSocket connection established for user: {user_address}")
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket for {user_address}: {e}")
            raise
    
    def disconnect(self, user_address: str):
        """Disconnect a WebSocket connection"""
        try:
            if user_address in self.active_connections:
                del self.active_connections[user_address]
            
            # Update user status
            if user_address in self.user_status:
                self.user_status[user_address].update({
                    "is_online": False,
                    "last_seen": datetime.utcnow()
                })
            
            # Notify other users about offline status (async task)
            # Note: In a real implementation, you'd want to handle this properly
            # For now, we'll just log it
            logger.info(f"WebSocket disconnected for user: {user_address}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket for {user_address}: {e}")
    
    async def send_personal_message(self, message: dict, user_address: str):
        """Send a message to a specific user"""
        try:
            websocket = self.active_connections.get(user_address)
            if websocket:
                # Add timestamp to message
                message["timestamp"] = datetime.utcnow().isoformat()
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Sent message to {user_address}: {message.get('type', 'unknown')}")
                return True
            else:
                logger.warning(f"User {user_address} not connected, message not sent")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send message to {user_address}: {e}")
            # Remove broken connection
            if user_address in self.active_connections:
                del self.active_connections[user_address]
            return False
    
    async def send_message_to_multiple(self, message: dict, user_addresses: Set[str]):
        """Send a message to multiple users"""
        successful_sends = 0
        for user_address in user_addresses:
            if await self.send_personal_message(message, user_address):
                successful_sends += 1
        return successful_sends
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected users"""
        if not self.active_connections:
            return 0
        
        user_addresses = set(self.active_connections.keys())
        return await self.send_message_to_multiple(message, user_addresses)
    
    async def notify_new_message(self, sender_address: str, recipient_address: str, message_id: str):
        """Notify recipient of a new message"""
        notification = {
            "type": "new_message",
            "sender": sender_address,
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.send_personal_message(notification, recipient_address)
    
    async def notify_message_read(self, sender_address: str, message_id: str, read_by: str):
        """Notify sender that their message was read"""
        notification = {
            "type": "message_read",
            "message_id": message_id,
            "read_by": read_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.send_personal_message(notification, sender_address)
    
    async def send_typing_indicator(self, sender_address: str, recipient_address: str, is_typing: bool):
        """Send typing indicator to recipient"""
        typing_message = {
            "type": "typing",
            "sender": sender_address,
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.send_personal_message(typing_message, recipient_address)
    
    async def _broadcast_user_status(self, user_address: str, is_online: bool):
        """Broadcast user online/offline status to relevant users"""
        # In a real implementation, you would only notify users who have
        # this user in their contact list or active chats
        # For simplicity, we'll just log this event
        status_message = {
            "type": "user_status",
            "user_address": user_address,
            "is_online": is_online,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"User {user_address} is now {'online' if is_online else 'offline'}")
        
        # In a full implementation, you would:
        # 1. Get the user's contact list or active chat participants
        # 2. Send status update only to those users
        # For now, we'll skip this to keep the MVP simple
    
    def get_user_status(self, user_address: str) -> Dict:
        """Get user online status"""
        return self.user_status.get(user_address, {
            "is_online": False,
            "last_seen": None
        })
    
    def get_online_users(self) -> Set[str]:
        """Get list of currently online users"""
        return set(self.active_connections.keys())
    
    def is_user_online(self, user_address: str) -> bool:
        """Check if a user is currently online"""
        return user_address in self.active_connections
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        online_count = len(self.active_connections)
        total_users = len(self.user_status)
        
        return {
            "online_users": online_count,
            "total_users": total_users,
            "active_connections": list(self.active_connections.keys()),
            "user_status_summary": {
                addr: status.get("is_online", False) 
                for addr, status in self.user_status.items()
            }
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()