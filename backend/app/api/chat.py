"""
Silexa Chat API Routes
Handles chat rooms, conversation history, and real-time chat features
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from backend.app.models import ChatRoom, ChatHistory, ApiResponse, TypingIndicator
from backend.app.services.messaging_service import messaging_service
from backend.app.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/rooms/{user_address}", response_model=ApiResponse)
async def get_user_chat_rooms(user_address: str):
    """
    Get all chat rooms for a user
    
    Args:
        user_address: User's Algorand address
        
    Returns:
        ApiResponse with user's chat rooms
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
        
        # Get chat rooms from messaging service
        chat_rooms = messaging_service.get_user_chats(user_address)
        
        # Convert to response format and add online status
        rooms_data = []
        for room in chat_rooms:
            # Get the other participant
            other_participant = None
            for participant in room.participants:
                if participant != user_address:
                    other_participant = participant
                    break
            
            other_user = None
            if other_participant:
                other_user = users_db.get(other_participant)
            
            room_data = {
                "id": room.id,
                "participants": room.participants,
                "created_at": room.created_at.isoformat(),
                "last_message_at": room.last_message_at.isoformat() if room.last_message_at else None,
                "last_message": {
                    "id": room.last_message.id,
                    "sender_address": room.last_message.sender_address,
                    "message_type": room.last_message.message_type.value,
                    "created_at": room.last_message.created_at.isoformat(),
                    "status": room.last_message.status.value
                } if room.last_message else None,
                "other_user": {
                    "address": other_participant,
                    "username": other_user.username if other_user else "Unknown",
                    "is_online": websocket_manager.is_user_online(other_participant) if other_participant else False
                } if other_participant else None
            }
            rooms_data.append(room_data)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(rooms_data)} chat rooms",
            data={
                "chat_rooms": rooms_data,
                "count": len(rooms_data)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user chat rooms: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user chat rooms"
        )


@router.get("/history/{user_address}/{other_address}", response_model=ApiResponse)
async def get_chat_history(
    user_address: str,
    other_address: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum messages"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get chat history between two users
    
    Args:
        user_address: Current user's Algorand address
        other_address: Other user's Algorand address
        limit: Maximum number of messages
        offset: Offset for pagination
        
    Returns:
        ApiResponse with chat history
    """
    try:
        # Validate users exist
        from backend.app.api.auth import users_db
        user = users_db.get(user_address)
        other_user = users_db.get(other_address)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not other_user:
            raise HTTPException(status_code=404, detail="Other user not found")
        
        # Get chat history from messaging service
        chat_history = messaging_service.get_chat_history(
            user_address=user_address,
            other_address=other_address,
            limit=limit,
            offset=offset
        )
        
        if not chat_history:
            # Return empty history if no messages found
            return ApiResponse(
                success=True,
                message="No messages found",
                data={
                    "chat_room_id": messaging_service._get_chat_room_id(user_address, other_address),
                    "messages": [],
                    "total_count": 0,
                    "has_more": False,
                    "other_user": {
                        "address": other_address,
                        "username": other_user.username,
                        "is_online": websocket_manager.is_user_online(other_address)
                    }
                }
            )
        
        # Convert messages to response format
        messages_data = []
        for message in chat_history.messages:
            message_data = {
                "id": message.id,
                "sender_address": message.sender_address,
                "recipient_address": message.recipient_address,
                "message_type": message.message_type.value,
                "status": message.status.value,
                "created_at": message.created_at.isoformat(),
                "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
                "read_at": message.read_at.isoformat() if message.read_at else None,
                "is_sent": message.sender_address == user_address
            }
            messages_data.append(message_data)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(messages_data)} messages",
            data={
                "chat_room_id": chat_history.chat_room_id,
                "messages": messages_data,
                "total_count": chat_history.total_count,
                "has_more": chat_history.has_more,
                "limit": limit,
                "offset": offset,
                "other_user": {
                    "address": other_address,
                    "username": other_user.username,
                    "is_online": websocket_manager.is_user_online(other_address)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get chat history"
        )


@router.post("/typing", response_model=ApiResponse)
async def send_typing_indicator(typing_data: TypingIndicator):
    """
    Send typing indicator to another user
    
    Args:
        typing_data: Typing indicator data
        
    Returns:
        ApiResponse with result
    """
    try:
        # Validate users exist
        from backend.app.api.auth import users_db
        user = users_db.get(typing_data.user_address)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Extract recipient from chat room ID or use a direct recipient field
        # For simplicity, we'll extract from the chat room ID
        chat_room_parts = typing_data.chat_room_id.replace("chat_", "").split("_")
        recipient_address = None
        
        for part in chat_room_parts:
            if part != typing_data.user_address:
                recipient_address = part
                break
        
        if not recipient_address:
            raise HTTPException(status_code=400, detail="Invalid chat room ID")
        
        # Send typing indicator via WebSocket
        success = await websocket_manager.send_typing_indicator(
            sender_address=typing_data.user_address,
            recipient_address=recipient_address,
            is_typing=typing_data.is_typing
        )
        
        return ApiResponse(
            success=True,
            message="Typing indicator sent" if success else "Recipient not online",
            data={
                "sent": success,
                "recipient_online": websocket_manager.is_user_online(recipient_address)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send typing indicator: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send typing indicator"
        )


@router.get("/room/{chat_room_id}", response_model=ApiResponse)
async def get_chat_room_info(chat_room_id: str):
    """
    Get chat room information
    
    Args:
        chat_room_id: Chat room ID
        
    Returns:
        ApiResponse with chat room information
    """
    try:
        chat_room = messaging_service.chat_rooms.get(chat_room_id)
        
        if not chat_room:
            raise HTTPException(
                status_code=404,
                detail="Chat room not found"
            )
        
        # Get participant information
        from backend.app.api.auth import users_db
        participants_info = []
        for participant_address in chat_room.participants:
            user = users_db.get(participant_address)
            if user:
                participant_info = {
                    "address": participant_address,
                    "username": user.username,
                    "is_online": websocket_manager.is_user_online(participant_address),
                    "last_seen": user.last_seen.isoformat() if user.last_seen else None
                }
                participants_info.append(participant_info)
        
        room_data = {
            "id": chat_room.id,
            "participants": chat_room.participants,
            "participants_info": participants_info,
            "created_at": chat_room.created_at.isoformat(),
            "last_message_at": chat_room.last_message_at.isoformat() if chat_room.last_message_at else None,
            "last_message": {
                "id": chat_room.last_message.id,
                "sender_address": chat_room.last_message.sender_address,
                "message_type": chat_room.last_message.message_type.value,
                "created_at": chat_room.last_message.created_at.isoformat(),
                "status": chat_room.last_message.status.value
            } if chat_room.last_message else None
        }
        
        return ApiResponse(
            success=True,
            message="Chat room info retrieved",
            data=room_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat room info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get chat room info"
        )


@router.get("/stats/{user_address}", response_model=ApiResponse)
async def get_chat_stats(user_address: str):
    """
    Get chat statistics for a user
    
    Args:
        user_address: User's Algorand address
        
    Returns:
        ApiResponse with chat statistics
    """
    try:
        # Validate user exists
        from backend.app.api.auth import users_db
        user = users_db.get(user_address)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Calculate statistics
        total_messages_sent = 0
        total_messages_received = 0
        unread_messages = 0
        
        for message in messaging_service.messages.values():
            if message.sender_address == user_address:
                total_messages_sent += 1
            elif message.recipient_address == user_address:
                total_messages_received += 1
                if message.status != "read":
                    unread_messages += 1
        
        chat_rooms = messaging_service.get_user_chats(user_address)
        
        stats = {
            "total_chat_rooms": len(chat_rooms),
            "total_messages_sent": total_messages_sent,
            "total_messages_received": total_messages_received,
            "unread_messages": unread_messages,
            "is_online": websocket_manager.is_user_online(user_address)
        }
        
        return ApiResponse(
            success=True,
            message="Chat statistics retrieved",
            data=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get chat stats"
        )