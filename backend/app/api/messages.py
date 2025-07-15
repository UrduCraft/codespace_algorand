"""
Silexa Messages API Routes
Handles message sending, receiving, and management
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, Optional
import logging

from backend.app.models import (
    MessageCreate, Message, MessageResponse, ApiResponse,
    MessageType, MessageStatus
)
from backend.app.services.messaging_service import messaging_service
from backend.app.services.encryption import EncryptionService
from backend.app.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/send", response_model=ApiResponse)
async def send_message(
    message_data: MessageCreate,
    sender_address: str = Body(..., description="Sender's Algorand address"),
    sender_private_key: str = Body(..., description="Sender's private key for signing")
):
    """
    Send a new message
    
    Args:
        message_data: Message content and metadata
        sender_address: Sender's Algorand address
        sender_private_key: Sender's private key for signing transactions
        
    Returns:
        ApiResponse with sent message information
    """
    try:
        # Validate sender exists
        from backend.app.api.auth import users_db
        sender = users_db.get(sender_address)
        if not sender:
            raise HTTPException(
                status_code=404,
                detail="Sender not found"
            )
        
        # Validate recipient exists
        recipient = users_db.get(message_data.recipient_address)
        if not recipient:
            raise HTTPException(
                status_code=404,
                detail="Recipient not found"
            )
        
        # Send message through messaging service
        sent_message = messaging_service.send_message(
            message_data=message_data,
            sender_address=sender_address,
            sender_private_key=sender_private_key
        )
        
        if not sent_message:
            raise HTTPException(
                status_code=500,
                detail="Failed to send message"
            )
        
        # Notify recipient via WebSocket if online
        await websocket_manager.notify_new_message(
            sender_address=sender_address,
            recipient_address=message_data.recipient_address,
            message_id=sent_message.id
        )
        
        logger.info(f"Message sent successfully: {sent_message.id}")
        
        return ApiResponse(
            success=True,
            message="Message sent successfully",
            data={
                "message_id": sent_message.id,
                "ipfs_hash": sent_message.ipfs_hash,
                "algorand_txn_id": sent_message.algorand_txn_id,
                "status": sent_message.status.value,
                "created_at": sent_message.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send message"
        )


@router.get("/receive/{message_id}", response_model=ApiResponse)
async def receive_message(
    message_id: str,
    recipient_address: str = Query(..., description="Recipient's Algorand address"),
    recipient_private_key: str = Query(..., description="Recipient's private key for decryption")
):
    """
    Receive and decrypt a message
    
    Args:
        message_id: Message ID to retrieve
        recipient_address: Recipient's Algorand address
        recipient_private_key: Recipient's private key for decryption
        
    Returns:
        ApiResponse with decrypted message content
    """
    try:
        # Validate recipient exists
        from backend.app.api.auth import users_db
        recipient = users_db.get(recipient_address)
        if not recipient:
            raise HTTPException(
                status_code=404,
                detail="Recipient not found"
            )
        
        # Receive message through messaging service
        message_result = messaging_service.receive_message(
            message_id=message_id,
            recipient_address=recipient_address,
            recipient_private_key=recipient_private_key
        )
        
        if not message_result:
            raise HTTPException(
                status_code=404,
                detail="Message not found or access denied"
            )
        
        message = message_result["message"]
        decrypted_content = message_result["decrypted_content"]
        
        # Notify sender that message was read via WebSocket
        await websocket_manager.notify_message_read(
            sender_address=message.sender_address,
            message_id=message_id,
            read_by=recipient_address
        )
        
        return ApiResponse(
            success=True,
            message="Message retrieved successfully",
            data={
                "message": {
                    "id": message.id,
                    "sender_address": message.sender_address,
                    "recipient_address": message.recipient_address,
                    "message_type": message.message_type.value,
                    "status": message.status.value,
                    "created_at": message.created_at.isoformat(),
                    "read_at": message.read_at.isoformat() if message.read_at else None,
                    "ipfs_hash": message.ipfs_hash,
                    "algorand_txn_id": message.algorand_txn_id
                },
                "decrypted_content": decrypted_content
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to receive message: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to receive message"
        )


@router.get("/list/{user_address}", response_model=ApiResponse)
async def list_user_messages(
    user_address: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    message_type: Optional[MessageType] = Query(None, description="Filter by message type"),
    status: Optional[MessageStatus] = Query(None, description="Filter by message status")
):
    """
    List messages for a user (sent and received)
    
    Args:
        user_address: User's Algorand address
        limit: Maximum number of results
        offset: Offset for pagination
        message_type: Filter by message type
        status: Filter by message status
        
    Returns:
        ApiResponse with messages list
    """
    try:
        # Validate user exists
        from backend.app.api.auth import users_db
        user = users_db.get(user_address)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Get messages from messaging service
        all_messages = []
        for message in messaging_service.messages.values():
            if (message.sender_address == user_address or 
                message.recipient_address == user_address):
                
                # Apply filters
                if message_type and message.message_type != message_type:
                    continue
                if status and message.status != status:
                    continue
                
                all_messages.append(message)
        
        # Sort by creation time (newest first)
        all_messages.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total_count = len(all_messages)
        paginated_messages = all_messages[offset:offset + limit]
        
        # Convert to response format
        messages_data = []
        for message in paginated_messages:
            message_data = {
                "id": message.id,
                "sender_address": message.sender_address,
                "recipient_address": message.recipient_address,
                "message_type": message.message_type.value,
                "status": message.status.value,
                "created_at": message.created_at.isoformat(),
                "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
                "read_at": message.read_at.isoformat() if message.read_at else None,
                "ipfs_hash": message.ipfs_hash,
                "algorand_txn_id": message.algorand_txn_id,
                "is_sent": message.sender_address == user_address
            }
            messages_data.append(message_data)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(messages_data)} messages",
            data={
                "messages": messages_data,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(messages_data) < total_count
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list user messages: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list user messages"
        )


@router.get("/info/{message_id}", response_model=ApiResponse)
async def get_message_info(message_id: str):
    """
    Get message information (metadata only, no decrypted content)
    
    Args:
        message_id: Message ID
        
    Returns:
        ApiResponse with message metadata
    """
    try:
        message = messaging_service.messages.get(message_id)
        
        if not message:
            raise HTTPException(
                status_code=404,
                detail="Message not found"
            )
        
        return ApiResponse(
            success=True,
            message="Message info retrieved",
            data={
                "id": message.id,
                "sender_address": message.sender_address,
                "recipient_address": message.recipient_address,
                "message_type": message.message_type.value,
                "status": message.status.value,
                "created_at": message.created_at.isoformat(),
                "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
                "read_at": message.read_at.isoformat() if message.read_at else None,
                "ipfs_hash": message.ipfs_hash,
                "algorand_txn_id": message.algorand_txn_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get message info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get message info"
        )


@router.post("/encrypt", response_model=ApiResponse)
async def encrypt_message_content(
    content: str = Body(..., description="Message content to encrypt"),
    sender_private_key: str = Body(..., description="Sender's private key"),
    recipient_public_key: str = Body(..., description="Recipient's public key")
):
    """
    Encrypt message content for sending
    
    Args:
        content: Message content to encrypt
        sender_private_key: Sender's private key for encryption
        recipient_public_key: Recipient's public key for encryption
        
    Returns:
        ApiResponse with encrypted content and nonce
    """
    try:
        # Verify keys
        if not EncryptionService.verify_public_key(recipient_public_key):
            raise HTTPException(
                status_code=400,
                detail="Invalid recipient public key"
            )
        
        # Encrypt the message
        encrypted_content, nonce = EncryptionService.encrypt_message(
            message=content,
            sender_private_key_b64=sender_private_key,
            recipient_public_key_b64=recipient_public_key
        )
        
        return ApiResponse(
            success=True,
            message="Message encrypted successfully",
            data={
                "encrypted_content": encrypted_content,
                "nonce": nonce
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to encrypt message: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to encrypt message"
        )


@router.post("/decrypt", response_model=ApiResponse)
async def decrypt_message_content(
    encrypted_content: str = Body(..., description="Encrypted message content"),
    nonce: str = Body(..., description="Encryption nonce"),
    recipient_private_key: str = Body(..., description="Recipient's private key"),
    sender_public_key: str = Body(..., description="Sender's public key")
):
    """
    Decrypt message content
    
    Args:
        encrypted_content: Encrypted message content
        nonce: Encryption nonce
        recipient_private_key: Recipient's private key for decryption
        sender_public_key: Sender's public key for decryption
        
    Returns:
        ApiResponse with decrypted content
    """
    try:
        # Verify keys
        if not EncryptionService.verify_public_key(sender_public_key):
            raise HTTPException(
                status_code=400,
                detail="Invalid sender public key"
            )
        
        # Decrypt the message
        decrypted_content = EncryptionService.decrypt_message(
            encrypted_message_b64=encrypted_content,
            nonce_b64=nonce,
            recipient_private_key_b64=recipient_private_key,
            sender_public_key_b64=sender_public_key
        )
        
        return ApiResponse(
            success=True,
            message="Message decrypted successfully",
            data={
                "decrypted_content": decrypted_content
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to decrypt message: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to decrypt message"
        )