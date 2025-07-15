"""
Silexa Users API Routes
Handles user management and contact operations
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from backend.app.models import UserProfile, UserUpdate, ApiResponse
from backend.app.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Import users database from auth module
from backend.app.api.auth import users_db


@router.get("/search", response_model=ApiResponse)
async def search_users(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Search for users by username or address
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        ApiResponse with search results
    """
    try:
        query_lower = query.lower()
        
        # Search users by username or address
        matching_users = []
        for user in users_db.values():
            if (query_lower in user.username.lower() or 
                query_lower in user.algorand_address.lower()):
                matching_users.append(user)
                
                if len(matching_users) >= limit:
                    break
        
        # Convert to dict and add online status
        results = []
        for user in matching_users:
            user_data = user.dict()
            user_data["is_online"] = websocket_manager.is_user_online(user.algorand_address)
            results.append(user_data)
        
        return ApiResponse(
            success=True,
            message=f"Found {len(results)} users",
            data={
                "users": results,
                "total": len(results),
                "query": query
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to search users: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search users"
        )


@router.get("/profile/{address}", response_model=ApiResponse)
async def get_user_profile(address: str):
    """
    Get detailed user profile
    
    Args:
        address: User's Algorand address
        
    Returns:
        ApiResponse with user profile
    """
    try:
        user = users_db.get(address)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Add real-time status
        user_data = user.dict()
        user_data["is_online"] = websocket_manager.is_user_online(address)
        user_status = websocket_manager.get_user_status(address)
        user_data.update(user_status)
        
        return ApiResponse(
            success=True,
            message="User profile retrieved",
            data=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user profile"
        )


@router.put("/profile/{address}", response_model=ApiResponse)
async def update_user_profile(address: str, user_update: UserUpdate):
    """
    Update user profile
    
    Args:
        address: User's Algorand address
        user_update: Updated user data
        
    Returns:
        ApiResponse with updated profile
    """
    try:
        user = users_db.get(address)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Update user fields
        if user_update.username is not None:
            user.username = user_update.username
        
        if user_update.public_key is not None:
            # Verify new public key
            from backend.app.services.encryption import EncryptionService
            if not EncryptionService.verify_public_key(user_update.public_key):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid public key format"
                )
            
            user.public_key = user_update.public_key
            
            # Update in messaging service
            from backend.app.services.messaging_service import messaging_service
            messaging_service.register_user_key(address, user_update.public_key)
        
        from datetime import datetime
        user.last_seen = datetime.utcnow()
        
        logger.info(f"User profile updated: {address}")
        
        return ApiResponse(
            success=True,
            message="User profile updated",
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user profile"
        )


@router.get("/online", response_model=ApiResponse)
async def get_online_users():
    """
    Get list of currently online users
    
    Returns:
        ApiResponse with online users list
    """
    try:
        online_addresses = websocket_manager.get_online_users()
        
        online_users = []
        for address in online_addresses:
            user = users_db.get(address)
            if user:
                user_data = user.dict()
                user_data["is_online"] = True
                online_users.append(user_data)
        
        return ApiResponse(
            success=True,
            message=f"Found {len(online_users)} online users",
            data={
                "users": online_users,
                "count": len(online_users)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get online users: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get online users"
        )


@router.get("/status/{address}", response_model=ApiResponse)
async def get_user_status(address: str):
    """
    Get user online status and last seen
    
    Args:
        address: User's Algorand address
        
    Returns:
        ApiResponse with user status
    """
    try:
        user = users_db.get(address)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Get real-time status
        is_online = websocket_manager.is_user_online(address)
        status = websocket_manager.get_user_status(address)
        
        return ApiResponse(
            success=True,
            message="User status retrieved",
            data={
                "address": address,
                "username": user.username,
                "is_online": is_online,
                "last_seen": user.last_seen.isoformat() if user.last_seen else None,
                **status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user status"
        )


@router.get("/list", response_model=ApiResponse)
async def list_all_users(
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    List all registered users (paginated)
    
    Args:
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        ApiResponse with users list
    """
    try:
        all_users = list(users_db.values())
        
        # Sort by creation date (newest first)
        all_users.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total_count = len(all_users)
        paginated_users = all_users[offset:offset + limit]
        
        # Add online status
        results = []
        for user in paginated_users:
            user_data = user.dict()
            user_data["is_online"] = websocket_manager.is_user_online(user.algorand_address)
            results.append(user_data)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(results)} users",
            data={
                "users": results,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(results) < total_count
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list users"
        )