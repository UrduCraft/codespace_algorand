"""
Silexa Authentication API Routes
Handles wallet connection and user authentication
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from backend.app.models import (
    WalletConnectRequest, UserCreate, UserProfile, 
    ApiResponse, ErrorResponse
)
from backend.app.services.algorand_service import algorand_service
from backend.app.services.messaging_service import messaging_service
from backend.app.services.encryption import EncryptionService

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory user store for MVP (use proper database in production)
users_db: Dict[str, UserProfile] = {}


@router.post("/connect-wallet", response_model=ApiResponse)
async def connect_wallet(wallet_request: WalletConnectRequest):
    """
    Connect and authenticate a wallet
    
    Args:
        wallet_request: Wallet connection request with signature
        
    Returns:
        ApiResponse with authentication result
    """
    try:
        # Verify wallet signature
        is_valid = algorand_service.verify_wallet_signature(wallet_request)
        
        if not is_valid:
            raise HTTPException(
                status_code=401, 
                detail="Invalid wallet signature"
            )
        
        # Get account info from Algorand
        account_info = algorand_service.get_account_info(wallet_request.address)
        
        if not account_info:
            raise HTTPException(
                status_code=404,
                detail="Algorand account not found"
            )
        
        # Check if user exists
        user = users_db.get(wallet_request.address)
        
        if user:
            # Update last seen
            from datetime import datetime
            user.last_seen = datetime.utcnow()
            user.is_online = True
        
        return ApiResponse(
            success=True,
            message="Wallet connected successfully",
            data={
                "address": wallet_request.address,
                "public_key": wallet_request.public_key,
                "account_info": account_info,
                "user_exists": user is not None,
                "user_profile": user.dict() if user else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect wallet: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to connect wallet"
        )


@router.post("/register", response_model=ApiResponse)
async def register_user(user_data: UserCreate):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        
    Returns:
        ApiResponse with registration result
    """
    try:
        # Check if user already exists
        if user_data.algorand_address in users_db:
            raise HTTPException(
                status_code=409,
                detail="User already registered"
            )
        
        # Verify public key format
        if not EncryptionService.verify_public_key(user_data.public_key):
            raise HTTPException(
                status_code=400,
                detail="Invalid public key format"
            )
        
        # Verify Algorand address exists
        account_info = algorand_service.get_account_info(user_data.algorand_address)
        if not account_info:
            raise HTTPException(
                status_code=404,
                detail="Algorand account not found"
            )
        
        # Create user profile
        from datetime import datetime
        user_profile = UserProfile(
            id=user_data.algorand_address,  # Use address as ID for MVP
            username=user_data.username,
            public_key=user_data.public_key,
            algorand_address=user_data.algorand_address,
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            is_online=True
        )
        
        # Store user in database
        users_db[user_data.algorand_address] = user_profile
        
        # Register encryption key in messaging service
        messaging_service.register_user_key(
            user_data.algorand_address,
            user_data.public_key
        )
        
        logger.info(f"User registered successfully: {user_data.algorand_address}")
        
        return ApiResponse(
            success=True,
            message="User registered successfully",
            data=user_profile.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to register user"
        )


@router.get("/profile/{address}", response_model=ApiResponse)
async def get_user_profile(address: str):
    """
    Get user profile by address
    
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
        
        return ApiResponse(
            success=True,
            message="User profile retrieved",
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user profile"
        )


@router.post("/logout/{address}", response_model=ApiResponse)
async def logout_user(address: str):
    """
    Logout user (update online status)
    
    Args:
        address: User's Algorand address
        
    Returns:
        ApiResponse with logout result
    """
    try:
        user = users_db.get(address)
        
        if user:
            from datetime import datetime
            user.is_online = False
            user.last_seen = datetime.utcnow()
        
        return ApiResponse(
            success=True,
            message="User logged out successfully",
            data={"address": address}
        )
        
    except Exception as e:
        logger.error(f"Failed to logout user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to logout user"
        )


@router.get("/verify/{address}", response_model=ApiResponse)
async def verify_user_session(address: str):
    """
    Verify if user session is valid
    
    Args:
        address: User's Algorand address
        
    Returns:
        ApiResponse with verification result
    """
    try:
        user = users_db.get(address)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User session not found"
            )
        
        # Check if account still exists on Algorand
        account_info = algorand_service.get_account_info(address)
        
        return ApiResponse(
            success=True,
            message="User session is valid",
            data={
                "user": user.dict(),
                "account_info": account_info
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify user session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to verify user session"
        )