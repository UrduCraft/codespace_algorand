"""
Silexa Backend - FastAPI Application
Main application entry point with API routes and WebSocket support
"""

import logging
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Set

from backend.config.settings import settings
from backend.app.api import auth, messages, users, chat
from backend.app.websocket_manager import websocket_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Silexa Backend")
    
    # Startup tasks
    try:
        # Test service connections
        from backend.app.services.ipfs_service import ipfs_service
        from backend.app.services.algorand_service import algorand_service
        
        if not ipfs_service.is_connected():
            logger.warning("IPFS service not connected - some features may not work")
        
        if not algorand_service.is_connected():
            logger.warning("Algorand service not connected - blockchain features may not work")
            
        logger.info("Silexa Backend started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down Silexa Backend")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Decentralized End-to-End Encrypted Messaging API",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= API Routes =============

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


# ============= WebSocket Endpoints =============

@app.websocket("/ws/{user_address}")
async def websocket_endpoint(websocket: WebSocket, user_address: str):
    """
    WebSocket endpoint for real-time messaging
    
    Args:
        user_address: User's Algorand address for identification
    """
    try:
        await websocket_manager.connect(websocket, user_address)
        logger.info(f"WebSocket connected for user: {user_address}")
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Handle different message types
                message_type = data.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await websocket_manager.send_personal_message(
                        {"type": "pong", "timestamp": data.get("timestamp")},
                        user_address
                    )
                
                elif message_type == "typing":
                    # Broadcast typing indicator to recipient
                    recipient = data.get("recipient")
                    if recipient:
                        await websocket_manager.send_personal_message(
                            {
                                "type": "typing",
                                "sender": user_address,
                                "is_typing": data.get("is_typing", False)
                            },
                            recipient
                        )
                
                elif message_type == "message_sent":
                    # Notify recipient of new message
                    recipient = data.get("recipient")
                    if recipient:
                        await websocket_manager.send_personal_message(
                            {
                                "type": "new_message",
                                "sender": user_address,
                                "message_id": data.get("message_id"),
                                "timestamp": data.get("timestamp")
                            },
                            recipient
                        )
                
                else:
                    logger.warning(f"Unknown WebSocket message type: {message_type}")
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user: {user_address}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_address}: {e}")
        finally:
            websocket_manager.disconnect(user_address)
            
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection for {user_address}: {e}")
        await websocket.close()


# ============= Error Handlers =============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else None
        }
    )


# ============= Service Status Endpoints =============

@app.get("/api/status/services")
async def get_service_status():
    """Get status of all services"""
    try:
        from backend.app.services.ipfs_service import ipfs_service
        from backend.app.services.algorand_service import algorand_service
        
        status = {
            "ipfs": {
                "connected": ipfs_service.is_connected(),
                "stats": ipfs_service.get_stats() if ipfs_service.is_connected() else None
            },
            "algorand": {
                "connected": algorand_service.is_connected(),
                "network_status": algorand_service.get_network_status() if algorand_service.is_connected() else None
            },
            "websocket": {
                "active_connections": len(websocket_manager.active_connections)
            }
        }
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service status")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )