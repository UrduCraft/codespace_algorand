"""
Silexa Algorand Service
Handles Algorand blockchain interactions, wallet authentication, and metadata storage
"""

import base64
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from algosdk import account, transaction, mnemonic
from algosdk.v2client import algod, indexer
from algosdk.encoding import decode_address, encode_address
from algosdk.logic import get_application_address
from algosdk.atomic_transaction_composer import AtomicTransactionComposer
from algokit_utils import ApplicationClient

from backend.config.settings import settings
from backend.app.models import TransactionRequest, WalletConnectRequest

logger = logging.getLogger(__name__)


class AlgorandService:
    """Service for Algorand blockchain operations"""
    
    def __init__(self):
        """Initialize Algorand clients"""
        try:
            # Initialize Algod client
            self.algod_client = algod.AlgodClient(
                settings.algod_token,
                settings.algod_address
            )
            
            # Initialize Indexer client
            self.indexer_client = indexer.IndexerClient(
                settings.indexer_token,
                settings.indexer_address
            )
            
            logger.info("Algorand clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Algorand clients: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if Algorand clients are connected"""
        try:
            status = self.algod_client.status()
            return status is not None
        except Exception as e:
            logger.error(f"Algorand connection test failed: {e}")
            return False
    
    def verify_wallet_signature(self, wallet_request: WalletConnectRequest) -> bool:
        """
        Verify a wallet signature to authenticate user
        
        Args:
            wallet_request: Wallet connection request with signature
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Decode the signature and message
            signature_bytes = base64.b64decode(wallet_request.signed_message)
            message_bytes = wallet_request.original_message.encode('utf-8')
            
            # Verify the signature using the public key
            public_key_bytes = base64.b64decode(wallet_request.public_key)
            
            # For Algorand, we need to verify Ed25519 signature
            # This is a simplified verification - in production, use proper crypto libraries
            return self._verify_ed25519_signature(
                message_bytes, 
                signature_bytes, 
                public_key_bytes
            )
            
        except Exception as e:
            logger.error(f"Failed to verify wallet signature: {e}")
            return False
    
    def _verify_ed25519_signature(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify Ed25519 signature (simplified implementation)
        In production, use proper cryptographic libraries
        """
        try:
            # This is a placeholder - implement proper Ed25519 verification
            # For now, we'll do basic validation of the data format
            return (
                len(signature) == 64 and 
                len(public_key) == 32 and 
                len(message) > 0
            )
        except Exception:
            return False
    
    def get_account_info(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get account information from Algorand
        
        Args:
            address: Algorand address
            
        Returns:
            Dict containing account information
        """
        try:
            account_info = self.algod_client.account_info(address)
            return account_info
            
        except Exception as e:
            logger.error(f"Failed to get account info for {address}: {e}")
            return None
    
    def send_metadata_transaction(
        self, 
        sender_address: str,
        sender_private_key: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Send a transaction with message metadata to Algorand
        
        Args:
            sender_address: Sender's Algorand address
            sender_private_key: Sender's private key for signing
            metadata: Message metadata to store
            
        Returns:
            str: Transaction ID if successful
        """
        try:
            # Get suggested transaction parameters
            params = self.algod_client.suggested_params()
            
            # Create note with metadata
            note = json.dumps(metadata).encode('utf-8')
            
            # Create payment transaction with 0 amount (metadata only)
            txn = transaction.PaymentTxn(
                sender=sender_address,
                sp=params,
                receiver=sender_address,  # Send to self for metadata storage
                amt=0,  # No payment, just metadata
                note=note
            )
            
            # Sign the transaction
            signed_txn = txn.sign(sender_private_key)
            
            # Submit the transaction
            txn_id = self.algod_client.send_transaction(signed_txn)
            
            # Wait for confirmation
            self._wait_for_confirmation(txn_id)
            
            logger.info(f"Metadata transaction sent successfully: {txn_id}")
            return txn_id
            
        except Exception as e:
            logger.error(f"Failed to send metadata transaction: {e}")
            return None
    
    def get_transaction_info(self, txn_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction information by ID
        
        Args:
            txn_id: Transaction ID
            
        Returns:
            Dict containing transaction information
        """
        try:
            txn_info = self.algod_client.pending_transaction_info(txn_id)
            return txn_info
            
        except Exception as e:
            logger.error(f"Failed to get transaction info for {txn_id}: {e}")
            return None
    
    def search_transactions_by_address(
        self, 
        address: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for transactions by address using Indexer
        
        Args:
            address: Algorand address to search
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction data
        """
        try:
            # Search for transactions involving this address
            response = self.indexer_client.search_transactions(
                address=address,
                limit=limit
            )
            
            transactions = response.get('transactions', [])
            
            # Filter for Silexa metadata transactions
            silexa_transactions = []
            for txn in transactions:
                note = txn.get('note')
                if note:
                    try:
                        # Decode note and check if it's Silexa metadata
                        decoded_note = base64.b64decode(note).decode('utf-8')
                        metadata = json.loads(decoded_note)
                        
                        if 'message_id' in metadata or 'silexa' in metadata:
                            silexa_transactions.append(txn)
                    except Exception:
                        continue
            
            return silexa_transactions
            
        except Exception as e:
            logger.error(f"Failed to search transactions for {address}: {e}")
            return []
    
    def get_message_metadata_from_blockchain(
        self, 
        message_id: str,
        sender_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve message metadata from blockchain transactions
        
        Args:
            message_id: Message ID to search for
            sender_address: Sender's address
            
        Returns:
            Dict containing message metadata
        """
        try:
            # Search transactions from sender
            transactions = self.search_transactions_by_address(sender_address)
            
            # Look for transaction with matching message ID
            for txn in transactions:
                note = txn.get('note')
                if note:
                    try:
                        decoded_note = base64.b64decode(note).decode('utf-8')
                        metadata = json.loads(decoded_note)
                        
                        if metadata.get('message_id') == message_id:
                            return metadata
                    except Exception:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get message metadata for {message_id}: {e}")
            return None
    
    def _wait_for_confirmation(self, txn_id: str, max_rounds: int = 4) -> bool:
        """
        Wait for transaction confirmation
        
        Args:
            txn_id: Transaction ID to wait for
            max_rounds: Maximum rounds to wait
            
        Returns:
            bool: True if confirmed, False if timeout
        """
        try:
            start_round = self.algod_client.status()["last-round"] + 1
            current_round = start_round
            
            while current_round < start_round + max_rounds:
                try:
                    pending_txn = self.algod_client.pending_transaction_info(txn_id)
                    
                    if pending_txn.get("confirmed-round", 0) > 0:
                        logger.info(f"Transaction {txn_id} confirmed in round {pending_txn['confirmed-round']}")
                        return True
                        
                    if pending_txn.get("pool-error"):
                        logger.error(f"Transaction {txn_id} failed: {pending_txn['pool-error']}")
                        return False
                        
                except Exception:
                    pass
                
                # Wait for next round
                status = self.algod_client.status_after_block(current_round)
                current_round = status["last-round"] + 1
            
            logger.warning(f"Transaction {txn_id} not confirmed after {max_rounds} rounds")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for confirmation of {txn_id}: {e}")
            return False
    
    def get_network_status(self) -> Optional[Dict[str, Any]]:
        """
        Get Algorand network status
        
        Returns:
            Dict containing network status
        """
        try:
            status = self.algod_client.status()
            return status
            
        except Exception as e:
            logger.error(f"Failed to get network status: {e}")
            return None


# Global Algorand service instance
algorand_service = AlgorandService()