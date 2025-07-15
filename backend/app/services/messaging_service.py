"""
Silexa Messaging Service
Orchestrates the complete message flow: encryption -> IPFS storage -> Algorand metadata
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from backend.app.models import (
    Message, MessageCreate, MessageType, MessageStatus, 
    IPFSMetadata, ChatRoom, ChatHistory
)
from backend.app.services.encryption import EncryptionService
from backend.app.services.ipfs_service import ipfs_service
from backend.app.services.algorand_service import algorand_service

logger = logging.getLogger(__name__)


class MessagingService:
    """Service for handling complete message lifecycle"""
    
    def __init__(self):
        """Initialize messaging service"""
        self.encryption_service = EncryptionService()
        # In a real application, you'd use a proper database
        # For this MVP, we'll use in-memory storage
        self.messages: Dict[str, Message] = {}
        self.chat_rooms: Dict[str, ChatRoom] = {}
        self.user_keys: Dict[str, str] = {}  # address -> public_key mapping
    
    def register_user_key(self, address: str, public_key: str) -> bool:
        """
        Register a user's public key for encryption
        
        Args:
            address: User's Algorand address
            public_key: User's encryption public key
            
        Returns:
            bool: True if successful
        """
        try:
            # Verify the public key is valid
            if not self.encryption_service.verify_public_key(public_key):
                return False
            
            self.user_keys[address] = public_key
            logger.info(f"Registered public key for user {address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register user key: {e}")
            return False
    
    def send_message(
        self, 
        message_data: MessageCreate,
        sender_address: str,
        sender_private_key: str
    ) -> Optional[Message]:
        """
        Send a message through the complete Silexa flow
        
        Args:
            message_data: Message content and metadata
            sender_address: Sender's Algorand address
            sender_private_key: Sender's private key for signing transactions
            
        Returns:
            Message: Complete message object if successful
        """
        try:
            # Generate unique message ID
            message_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Get recipient's public key
            recipient_public_key = self.user_keys.get(message_data.recipient_address)
            if not recipient_public_key:
                logger.error(f"Public key not found for recipient {message_data.recipient_address}")
                return None
            
            # Create IPFS metadata
            ipfs_metadata = IPFSMetadata(
                message_id=message_id,
                sender_address=sender_address,
                recipient_address=message_data.recipient_address,
                timestamp=current_time,
                content_type="text/plain",
                encrypted=True
            )
            
            # Upload encrypted message to IPFS
            ipfs_result = ipfs_service.upload_message(
                encrypted_content=message_data.content,
                metadata=ipfs_metadata
            )
            
            if not ipfs_result:
                logger.error("Failed to upload message to IPFS")
                return None
            
            # Create metadata for Algorand transaction
            algorand_metadata = {
                "silexa": True,
                "message_id": message_id,
                "ipfs_hash": ipfs_result.hash,
                "recipient_address": message_data.recipient_address,
                "message_type": message_data.message_type.value,
                "timestamp": current_time.isoformat()
            }
            
            # Send metadata transaction to Algorand
            txn_id = algorand_service.send_metadata_transaction(
                sender_address=sender_address,
                sender_private_key=sender_private_key,
                metadata=algorand_metadata
            )
            
            if not txn_id:
                logger.error("Failed to send metadata transaction to Algorand")
                return None
            
            # Create complete message object
            message = Message(
                id=message_id,
                sender_address=sender_address,
                recipient_address=message_data.recipient_address,
                content=message_data.content,  # Encrypted content
                message_type=message_data.message_type,
                nonce=message_data.nonce,
                ipfs_hash=ipfs_result.hash,
                algorand_txn_id=txn_id,
                status=MessageStatus.SENT,
                created_at=current_time,
                metadata=message_data.metadata
            )
            
            # Store message in local cache
            self.messages[message_id] = message
            
            # Update or create chat room
            self._update_chat_room(sender_address, message_data.recipient_address, message)
            
            logger.info(f"Message sent successfully: {message_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None
    
    def receive_message(
        self, 
        message_id: str,
        recipient_address: str,
        recipient_private_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt a message for the recipient
        
        Args:
            message_id: Message ID to retrieve
            recipient_address: Recipient's Algorand address
            recipient_private_key: Recipient's private key for decryption
            
        Returns:
            Dict with message and decrypted content
        """
        try:
            # Check local cache first
            message = self.messages.get(message_id)
            
            if not message:
                # Try to reconstruct from blockchain and IPFS
                message = self._reconstruct_message_from_blockchain(message_id)
                
                if not message:
                    logger.error(f"Message {message_id} not found")
                    return None
            
            # Verify recipient
            if message.recipient_address != recipient_address:
                logger.error(f"Unauthorized access attempt to message {message_id}")
                return None
            
            # Get sender's public key for decryption
            sender_public_key = self.user_keys.get(message.sender_address)
            if not sender_public_key:
                logger.error(f"Sender public key not found for message {message_id}")
                return None
            
            # Decrypt the message content
            try:
                decrypted_content = self.encryption_service.decrypt_message(
                    encrypted_message_b64=message.content,
                    nonce_b64=message.nonce,
                    recipient_private_key_b64=recipient_private_key,
                    sender_public_key_b64=sender_public_key
                )
                
                # Mark message as delivered/read
                message.status = MessageStatus.READ
                message.read_at = datetime.utcnow()
                
                return {
                    "message": message,
                    "decrypted_content": decrypted_content
                }
                
            except Exception as e:
                logger.error(f"Failed to decrypt message {message_id}: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to receive message {message_id}: {e}")
            return None
    
    def get_chat_history(
        self, 
        user_address: str,
        other_address: str,
        limit: int = 50,
        offset: int = 0
    ) -> Optional[ChatHistory]:
        """
        Get chat history between two users
        
        Args:
            user_address: Current user's address
            other_address: Other user's address
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            ChatHistory object with messages
        """
        try:
            # Get or create chat room
            chat_room_id = self._get_chat_room_id(user_address, other_address)
            chat_room = self.chat_rooms.get(chat_room_id)
            
            if not chat_room:
                # Try to reconstruct from blockchain
                self._reconstruct_chat_from_blockchain(user_address, other_address)
                chat_room = self.chat_rooms.get(chat_room_id)
            
            # Filter messages for this chat
            chat_messages = [
                msg for msg in self.messages.values()
                if (msg.sender_address == user_address and msg.recipient_address == other_address) or
                   (msg.sender_address == other_address and msg.recipient_address == user_address)
            ]
            
            # Sort by creation time
            chat_messages.sort(key=lambda x: x.created_at)
            
            # Apply pagination
            total_count = len(chat_messages)
            paginated_messages = chat_messages[offset:offset + limit]
            has_more = offset + len(paginated_messages) < total_count
            
            return ChatHistory(
                chat_room_id=chat_room_id,
                messages=paginated_messages,
                total_count=total_count,
                has_more=has_more
            )
            
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return None
    
    def get_user_chats(self, user_address: str) -> List[ChatRoom]:
        """
        Get all chat rooms for a user
        
        Args:
            user_address: User's Algorand address
            
        Returns:
            List of chat rooms
        """
        try:
            user_chats = [
                chat for chat in self.chat_rooms.values()
                if user_address in chat.participants
            ]
            
            # Sort by last message time
            user_chats.sort(key=lambda x: x.last_message_at or x.created_at, reverse=True)
            
            return user_chats
            
        except Exception as e:
            logger.error(f"Failed to get user chats: {e}")
            return []
    
    def _get_chat_room_id(self, address1: str, address2: str) -> str:
        """Generate consistent chat room ID for two addresses"""
        # Sort addresses to ensure consistent ID regardless of order
        sorted_addresses = sorted([address1, address2])
        return f"chat_{sorted_addresses[0]}_{sorted_addresses[1]}"
    
    def _update_chat_room(self, sender_address: str, recipient_address: str, message: Message):
        """Update or create chat room with new message"""
        try:
            chat_room_id = self._get_chat_room_id(sender_address, recipient_address)
            
            if chat_room_id in self.chat_rooms:
                # Update existing chat room
                chat_room = self.chat_rooms[chat_room_id]
                chat_room.last_message_at = message.created_at
                chat_room.last_message = message
            else:
                # Create new chat room
                chat_room = ChatRoom(
                    id=chat_room_id,
                    participants=[sender_address, recipient_address],
                    created_at=message.created_at,
                    last_message_at=message.created_at,
                    last_message=message
                )
                self.chat_rooms[chat_room_id] = chat_room
                
        except Exception as e:
            logger.error(f"Failed to update chat room: {e}")
    
    def _reconstruct_message_from_blockchain(self, message_id: str) -> Optional[Message]:
        """
        Reconstruct a message from blockchain metadata and IPFS content
        This would be implemented for message persistence and recovery
        """
        # This is a placeholder for blockchain-based message reconstruction
        # In a full implementation, you would:
        # 1. Search blockchain transactions for message metadata
        # 2. Retrieve encrypted content from IPFS
        # 3. Reconstruct the Message object
        return None
    
    def _reconstruct_chat_from_blockchain(self, address1: str, address2: str):
        """
        Reconstruct chat history from blockchain transactions
        This would be implemented for chat persistence and recovery
        """
        # This is a placeholder for blockchain-based chat reconstruction
        pass


# Global messaging service instance
messaging_service = MessagingService()