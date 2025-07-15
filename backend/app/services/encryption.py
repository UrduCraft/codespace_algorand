"""
Silexa Encryption Service
Provides end-to-end encryption using libsodium (PyNaCl)
Uses X25519 key exchange and XSalsa20Poly1305 for encryption
"""

import os
import base64
from typing import Tuple, Optional
from nacl.public import PrivateKey, PublicKey, Box
from nacl.utils import random
from nacl.encoding import Base64Encoder, HexEncoder
from nacl.exceptions import CryptoError
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for handling end-to-end encryption using libsodium"""
    
    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """
        Generate a new X25519 key pair for encryption
        
        Returns:
            Tuple[str, str]: (private_key_b64, public_key_b64)
        """
        try:
            private_key = PrivateKey.generate()
            public_key = private_key.public_key
            
            private_key_b64 = private_key.encode(encoder=Base64Encoder).decode('utf-8')
            public_key_b64 = public_key.encode(encoder=Base64Encoder).decode('utf-8')
            
            return private_key_b64, public_key_b64
        except Exception as e:
            logger.error(f"Failed to generate keypair: {e}")
            raise
    
    @staticmethod
    def encrypt_message(
        message: str, 
        sender_private_key_b64: str, 
        recipient_public_key_b64: str
    ) -> Tuple[str, str]:
        """
        Encrypt a message using sender's private key and recipient's public key
        
        Args:
            message: The plaintext message to encrypt
            sender_private_key_b64: Sender's private key (base64 encoded)
            recipient_public_key_b64: Recipient's public key (base64 encoded)
            
        Returns:
            Tuple[str, str]: (encrypted_message_b64, nonce_b64)
        """
        try:
            # Decode keys from base64
            sender_private_key = PrivateKey(
                sender_private_key_b64.encode(), 
                encoder=Base64Encoder
            )
            recipient_public_key = PublicKey(
                recipient_public_key_b64.encode(), 
                encoder=Base64Encoder
            )
            
            # Create encryption box
            box = Box(sender_private_key, recipient_public_key)
            
            # Encrypt the message
            encrypted = box.encrypt(message.encode('utf-8'))
            
            # Extract nonce and ciphertext
            nonce_b64 = base64.b64encode(encrypted.nonce).decode('utf-8')
            ciphertext_b64 = base64.b64encode(encrypted.ciphertext).decode('utf-8')
            
            return ciphertext_b64, nonce_b64
            
        except Exception as e:
            logger.error(f"Failed to encrypt message: {e}")
            raise
    
    @staticmethod
    def decrypt_message(
        encrypted_message_b64: str,
        nonce_b64: str,
        recipient_private_key_b64: str,
        sender_public_key_b64: str
    ) -> str:
        """
        Decrypt a message using recipient's private key and sender's public key
        
        Args:
            encrypted_message_b64: Encrypted message (base64 encoded)
            nonce_b64: Encryption nonce (base64 encoded)
            recipient_private_key_b64: Recipient's private key (base64 encoded)
            sender_public_key_b64: Sender's public key (base64 encoded)
            
        Returns:
            str: Decrypted plaintext message
        """
        try:
            # Decode keys from base64
            recipient_private_key = PrivateKey(
                recipient_private_key_b64.encode(), 
                encoder=Base64Encoder
            )
            sender_public_key = PublicKey(
                sender_public_key_b64.encode(), 
                encoder=Base64Encoder
            )
            
            # Create decryption box
            box = Box(recipient_private_key, sender_public_key)
            
            # Decode encrypted data
            nonce = base64.b64decode(nonce_b64.encode('utf-8'))
            ciphertext = base64.b64decode(encrypted_message_b64.encode('utf-8'))
            
            # Decrypt the message
            decrypted_bytes = box.decrypt(ciphertext, nonce)
            decrypted_message = decrypted_bytes.decode('utf-8')
            
            return decrypted_message
            
        except CryptoError as e:
            logger.error(f"Decryption failed - invalid keys or corrupted data: {e}")
            raise ValueError("Failed to decrypt message - invalid keys or corrupted data")
        except Exception as e:
            logger.error(f"Failed to decrypt message: {e}")
            raise
    
    @staticmethod
    def encrypt_file(
        file_data: bytes,
        sender_private_key_b64: str,
        recipient_public_key_b64: str
    ) -> Tuple[bytes, str]:
        """
        Encrypt file data for secure transmission
        
        Args:
            file_data: Raw file bytes
            sender_private_key_b64: Sender's private key (base64 encoded)
            recipient_public_key_b64: Recipient's public key (base64 encoded)
            
        Returns:
            Tuple[bytes, str]: (encrypted_data, nonce_b64)
        """
        try:
            # Decode keys from base64
            sender_private_key = PrivateKey(
                sender_private_key_b64.encode(), 
                encoder=Base64Encoder
            )
            recipient_public_key = PublicKey(
                recipient_public_key_b64.encode(), 
                encoder=Base64Encoder
            )
            
            # Create encryption box
            box = Box(sender_private_key, recipient_public_key)
            
            # Encrypt the file data
            encrypted = box.encrypt(file_data)
            
            # Extract nonce and return encrypted data
            nonce_b64 = base64.b64encode(encrypted.nonce).decode('utf-8')
            
            return encrypted.ciphertext, nonce_b64
            
        except Exception as e:
            logger.error(f"Failed to encrypt file: {e}")
            raise
    
    @staticmethod
    def decrypt_file(
        encrypted_data: bytes,
        nonce_b64: str,
        recipient_private_key_b64: str,
        sender_public_key_b64: str
    ) -> bytes:
        """
        Decrypt file data
        
        Args:
            encrypted_data: Encrypted file bytes
            nonce_b64: Encryption nonce (base64 encoded)
            recipient_private_key_b64: Recipient's private key (base64 encoded)
            sender_public_key_b64: Sender's public key (base64 encoded)
            
        Returns:
            bytes: Decrypted file data
        """
        try:
            # Decode keys from base64
            recipient_private_key = PrivateKey(
                recipient_private_key_b64.encode(), 
                encoder=Base64Encoder
            )
            sender_public_key = PublicKey(
                sender_public_key_b64.encode(), 
                encoder=Base64Encoder
            )
            
            # Create decryption box
            box = Box(recipient_private_key, sender_public_key)
            
            # Decode nonce
            nonce = base64.b64decode(nonce_b64.encode('utf-8'))
            
            # Decrypt the file data
            decrypted_data = box.decrypt(encrypted_data, nonce)
            
            return decrypted_data
            
        except CryptoError as e:
            logger.error(f"File decryption failed: {e}")
            raise ValueError("Failed to decrypt file - invalid keys or corrupted data")
        except Exception as e:
            logger.error(f"Failed to decrypt file: {e}")
            raise
    
    @staticmethod
    def verify_public_key(public_key_b64: str) -> bool:
        """
        Verify if a public key is valid
        
        Args:
            public_key_b64: Public key to verify (base64 encoded)
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            PublicKey(public_key_b64.encode(), encoder=Base64Encoder)
            return True
        except Exception:
            return False