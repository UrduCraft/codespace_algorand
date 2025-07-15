"""
Silexa IPFS Service
Handles IPFS operations for decentralized storage of encrypted messages and files
"""

import ipfshttpclient
import json
import io
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import logging
from backend.config.settings import settings
from backend.app.models import IPFSUploadResponse, IPFSMetadata

logger = logging.getLogger(__name__)


class IPFSService:
    """Service for interacting with IPFS for decentralized storage"""
    
    def __init__(self):
        """Initialize IPFS client"""
        try:
            if settings.ipfs_infura_project_id and settings.ipfs_infura_secret:
                # Use Infura IPFS for production
                self.client = ipfshttpclient.connect(
                    multiaddr=f"/dns/ipfs.infura.io/tcp/5001/https",
                    auth=(settings.ipfs_infura_project_id, settings.ipfs_infura_secret)
                )
                logger.info("Connected to Infura IPFS")
            else:
                # Use local IPFS node
                self.client = ipfshttpclient.connect(
                    addr=f"{settings.ipfs_protocol}://{settings.ipfs_host}:{settings.ipfs_port}"
                )
                logger.info("Connected to local IPFS node")
                
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if IPFS client is connected"""
        try:
            if self.client is None:
                return False
            # Test connection with a simple ID call
            self.client.id()
            return True
        except Exception as e:
            logger.error(f"IPFS connection test failed: {e}")
            return False
    
    def upload_message(
        self, 
        encrypted_content: str,
        metadata: IPFSMetadata
    ) -> Optional[IPFSUploadResponse]:
        """
        Upload an encrypted message to IPFS
        
        Args:
            encrypted_content: The encrypted message content
            metadata: Message metadata
            
        Returns:
            IPFSUploadResponse: Upload result with IPFS hash
        """
        try:
            if not self.is_connected():
                raise Exception("IPFS client not connected")
            
            # Create message object with metadata
            message_object = {
                "content": encrypted_content,
                "metadata": {
                    "message_id": metadata.message_id,
                    "sender_address": metadata.sender_address,
                    "recipient_address": metadata.recipient_address,
                    "timestamp": metadata.timestamp.isoformat(),
                    "content_type": metadata.content_type,
                    "encrypted": metadata.encrypted
                }
            }
            
            # Convert to JSON and upload
            json_data = json.dumps(message_object, indent=2)
            file_obj = io.StringIO(json_data)
            
            result = self.client.add(file_obj, pin=True)
            
            logger.info(f"Message uploaded to IPFS with hash: {result['Hash']}")
            
            return IPFSUploadResponse(
                hash=result['Hash'],
                size=result['Size'],
                name=f"message_{metadata.message_id}.json"
            )
            
        except Exception as e:
            logger.error(f"Failed to upload message to IPFS: {e}")
            return None
    
    def upload_file(
        self, 
        file_data: bytes,
        filename: str,
        metadata: IPFSMetadata
    ) -> Optional[IPFSUploadResponse]:
        """
        Upload an encrypted file to IPFS
        
        Args:
            file_data: Encrypted file bytes
            filename: Original filename
            metadata: File metadata
            
        Returns:
            IPFSUploadResponse: Upload result with IPFS hash
        """
        try:
            if not self.is_connected():
                raise Exception("IPFS client not connected")
            
            # Create file object with metadata
            file_object = {
                "data": file_data.hex(),  # Convert bytes to hex string
                "filename": filename,
                "metadata": {
                    "message_id": metadata.message_id,
                    "sender_address": metadata.sender_address,
                    "recipient_address": metadata.recipient_address,
                    "timestamp": metadata.timestamp.isoformat(),
                    "content_type": metadata.content_type,
                    "encrypted": metadata.encrypted
                }
            }
            
            # Convert to JSON and upload
            json_data = json.dumps(file_object, indent=2)
            file_obj = io.StringIO(json_data)
            
            result = self.client.add(file_obj, pin=True)
            
            logger.info(f"File uploaded to IPFS with hash: {result['Hash']}")
            
            return IPFSUploadResponse(
                hash=result['Hash'],
                size=result['Size'],
                name=filename
            )
            
        except Exception as e:
            logger.error(f"Failed to upload file to IPFS: {e}")
            return None
    
    def retrieve_message(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a message from IPFS
        
        Args:
            ipfs_hash: IPFS hash of the message
            
        Returns:
            Dict containing message content and metadata
        """
        try:
            if not self.is_connected():
                raise Exception("IPFS client not connected")
            
            # Retrieve file from IPFS
            data = self.client.cat(ipfs_hash)
            
            # Parse JSON content
            message_object = json.loads(data.decode('utf-8'))
            
            logger.info(f"Message retrieved from IPFS hash: {ipfs_hash}")
            
            return message_object
            
        except Exception as e:
            logger.error(f"Failed to retrieve message from IPFS {ipfs_hash}: {e}")
            return None
    
    def retrieve_file(self, ipfs_hash: str) -> Optional[Tuple[bytes, str, Dict[str, Any]]]:
        """
        Retrieve a file from IPFS
        
        Args:
            ipfs_hash: IPFS hash of the file
            
        Returns:
            Tuple[bytes, str, Dict]: (file_data, filename, metadata)
        """
        try:
            if not self.is_connected():
                raise Exception("IPFS client not connected")
            
            # Retrieve file from IPFS
            data = self.client.cat(ipfs_hash)
            
            # Parse JSON content
            file_object = json.loads(data.decode('utf-8'))
            
            # Convert hex string back to bytes
            file_data = bytes.fromhex(file_object['data'])
            filename = file_object['filename']
            metadata = file_object['metadata']
            
            logger.info(f"File retrieved from IPFS hash: {ipfs_hash}")
            
            return file_data, filename, metadata
            
        except Exception as e:
            logger.error(f"Failed to retrieve file from IPFS {ipfs_hash}: {e}")
            return None
    
    def pin_hash(self, ipfs_hash: str) -> bool:
        """
        Pin a hash to ensure it's not garbage collected
        
        Args:
            ipfs_hash: IPFS hash to pin
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_connected():
                raise Exception("IPFS client not connected")
            
            self.client.pin.add(ipfs_hash)
            logger.info(f"Pinned IPFS hash: {ipfs_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pin IPFS hash {ipfs_hash}: {e}")
            return False
    
    def unpin_hash(self, ipfs_hash: str) -> bool:
        """
        Unpin a hash to allow garbage collection
        
        Args:
            ipfs_hash: IPFS hash to unpin
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_connected():
                raise Exception("IPFS client not connected")
            
            self.client.pin.rm(ipfs_hash)
            logger.info(f"Unpinned IPFS hash: {ipfs_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unpin IPFS hash {ipfs_hash}: {e}")
            return False
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get IPFS node statistics
        
        Returns:
            Dict containing node stats
        """
        try:
            if not self.is_connected():
                return None
            
            stats = {
                "id": self.client.id(),
                "version": self.client.version(),
                "repo_stats": self.client.repo.stat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get IPFS stats: {e}")
            return None


# Global IPFS service instance
ipfs_service = IPFSService()