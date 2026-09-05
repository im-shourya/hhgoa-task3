import os
import json
import logging
from web3 import Web3
from web3.exceptions import ContractLogicError, TimeExhausted

from src.config import get_settings
from src.errors import BlockchainError, BlockchainTransactionError
from .models import BlockchainTransactionResult
from .client import BlockchainClient

logger = logging.getLogger(__name__)

class EvidenceRegistryClient:
    def __init__(self, client: BlockchainClient, contract_address: str = None):
        self.client = client
        self.w3 = client.get_w3()
        
        settings = get_settings()
        self.contract_address = contract_address or settings.blockchain_contract_address
        self.timeout = settings.blockchain_tx_timeout
        
        if not self.contract_address:
            raise BlockchainError("EvidenceRegistry contract address is required")
            
        self.abi = self._load_abi()
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
        
    def _load_abi(self) -> list:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        abi_path = os.path.join(project_root, "build", "contracts_EvidenceRegistry_sol_EvidenceRegistry.abi")
        
        if not os.path.exists(abi_path):
            raise BlockchainError(f"Contract ABI not found at {abi_path}. Did you compile it?")
            
        with open(abi_path, "r") as f:
            return json.load(f)
            
    def verify_evidence(self, evidence_hash: str) -> dict:
        """
        Check if evidence is registered on-chain.
        
        Args:
            evidence_hash (str): 64-character SHA-256 hex string
            
        Returns:
            dict: {"exists": bool, "timestamp": int, "submitter": str}
        """
        try:
            # Convert hex string to 32 bytes
            fingerprint = bytes.fromhex(evidence_hash)
            if len(fingerprint) != 32:
                raise ValueError("Evidence hash must be exactly 32 bytes (64 hex characters)")
                
            exists, timestamp, submitter = self.contract.functions.getEvidence(fingerprint).call()
            
            return {
                "exists": exists,
                "timestamp": timestamp,
                "submitter": submitter if exists else None
            }
        except Exception as e:
            logger.error(f"Failed to verify evidence {evidence_hash}: {e}")
            raise BlockchainError(f"Failed to verify evidence: {e}")

    def register_evidence(self, evidence_hash: str) -> BlockchainTransactionResult:
        """
        Register a cryptographic evidence hash on-chain.
        
        Args:
            evidence_hash (str): 64-character SHA-256 hex string
            
        Returns:
            BlockchainTransactionResult
        """
        if not self.client.account:
            raise BlockchainTransactionError("A private key must be configured to send transactions")
            
        try:
            # Convert hex string to 32 bytes
            fingerprint = bytes.fromhex(evidence_hash)
            if len(fingerprint) != 32:
                raise ValueError("Evidence hash must be exactly 32 bytes (64 hex characters)")
                
            # Pre-flight check: see if it already exists to save gas and avoid reverts
            if self.contract.functions.evidenceExists(fingerprint).call():
                logger.info(f"Evidence {evidence_hash} is already registered on-chain.")
                return BlockchainTransactionResult(
                    success=True,
                    evidence_hash=evidence_hash,
                    status="already_registered"
                )
                
            # Submit transaction
            logger.info(f"Registering evidence {evidence_hash} on-chain...")
            tx_hash = self.contract.functions.registerEvidence(fingerprint).transact()
            
            logger.info(f"Transaction submitted: {tx_hash.hex()}. Waiting for receipt...")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=self.timeout)
            
            if receipt.status != 1:
                raise BlockchainTransactionError(f"Transaction reverted. Hash: {tx_hash.hex()}")
                
            logger.info(f"Evidence successfully registered in block {receipt.blockNumber}")
            
            return BlockchainTransactionResult(
                success=True,
                evidence_hash=evidence_hash,
                transaction_hash=tx_hash.hex(),
                block_number=receipt.blockNumber,
                chain_id=self.w3.eth.chain_id,
                submitter=self.client.account.address,
                status="success"
            )
            
        except TimeExhausted:
            error_msg = f"Transaction timed out after {self.timeout} seconds"
            logger.error(error_msg)
            return BlockchainTransactionResult(
                success=False,
                evidence_hash=evidence_hash,
                status="failed",
                error=error_msg
            )
        except ContractLogicError as e:
            error_msg = f"Contract reverted: {e}"
            logger.error(error_msg)
            return BlockchainTransactionResult(
                success=False,
                evidence_hash=evidence_hash,
                status="failed",
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Unexpected transaction error: {e}"
            logger.error(error_msg)
            return BlockchainTransactionResult(
                success=False,
                evidence_hash=evidence_hash,
                status="failed",
                error=error_msg
            )
