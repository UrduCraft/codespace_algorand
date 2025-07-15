"""
Silexa Backend Configuration Settings
Handles environment variables and application configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    app_name: str = "Silexa Messaging API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Algorand Configuration
    algod_address: str = "https://testnet-api.algonode.cloud"
    algod_token: str = ""
    indexer_address: str = "https://testnet-idx.algonode.cloud"
    indexer_token: str = ""
    
    # IPFS Configuration
    ipfs_host: str = "127.0.0.1"
    ipfs_port: int = 5001
    ipfs_protocol: str = "http"
    # Alternative: Use Infura IPFS
    ipfs_infura_project_id: Optional[str] = None
    ipfs_infura_secret: Optional[str] = None
    
    # Security Configuration
    secret_key: str = "your-secret-key-here-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Database Configuration (for caching and user data)
    database_url: str = "sqlite:///./silexa.db"
    
    # Messaging Configuration
    max_message_size: int = 1024 * 1024  # 1MB
    message_retention_days: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()