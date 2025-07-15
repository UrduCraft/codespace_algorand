"""
Silexa Data Models and Schemas
Defines the data structures for users, messages, and API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"


class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


# ============= User Models =============

class UserCreate(BaseModel):
    """Model for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50)
    public_key: str = Field(..., description="Ed25519 public key for encryption")
    algorand_address: str = Field(..., description="Algorand wallet address")


class UserProfile(BaseModel):
    """Model for user profile information"""
    id: str
    username: str
    public_key: str
    algorand_address: str
    created_at: datetime
    last_seen: Optional[datetime] = None
    is_online: bool = False


class UserUpdate(BaseModel):
    """Model for updating user information"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    public_key: Optional[str] = None


# ============= Message Models =============

class MessageCreate(BaseModel):
    """Model for creating a new message"""
    recipient_address: str = Field(..., description="Recipient's Algorand address")
    content: str = Field(..., max_length=10000, description="Encrypted message content")
    message_type: MessageType = MessageType.TEXT
    nonce: str = Field(..., description="Encryption nonce")
    metadata: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    """Model for a complete message"""
    id: str
    sender_address: str
    recipient_address: str
    content: str  # Encrypted content
    message_type: MessageType
    nonce: str
    ipfs_hash: Optional[str] = None
    algorand_txn_id: Optional[str] = None
    status: MessageStatus
    created_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Model for message API responses"""
    message: Message
    decrypted_content: Optional[str] = None


# ============= Chat Models =============

class ChatRoom(BaseModel):
    """Model for a chat room between two users"""
    id: str
    participants: List[str]  # List of Algorand addresses
    created_at: datetime
    last_message_at: Optional[datetime] = None
    last_message: Optional[Message] = None


class ChatHistory(BaseModel):
    """Model for chat history"""
    chat_room_id: str
    messages: List[Message]
    total_count: int
    has_more: bool


# ============= Algorand Models =============

class WalletConnectRequest(BaseModel):
    """Model for wallet connection request"""
    address: str
    public_key: str
    signed_message: str
    original_message: str


class TransactionRequest(BaseModel):
    """Model for Algorand transaction requests"""
    sender: str
    receiver: str
    amount: int = 0  # For metadata transactions, amount is 0
    note: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============= IPFS Models =============

class IPFSUploadResponse(BaseModel):
    """Model for IPFS upload responses"""
    hash: str
    size: int
    name: Optional[str] = None


class IPFSMetadata(BaseModel):
    """Model for IPFS file metadata"""
    message_id: str
    sender_address: str
    recipient_address: str
    timestamp: datetime
    content_type: str
    encrypted: bool = True


# ============= API Response Models =============

class ApiResponse(BaseModel):
    """Generic API response model"""
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None


# ============= WebSocket Models =============

class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    type: str  # 'message', 'typing', 'status', etc.
    data: Dict[str, Any]
    sender: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TypingIndicator(BaseModel):
    """Model for typing indicators"""
    user_address: str
    chat_room_id: str
    is_typing: bool