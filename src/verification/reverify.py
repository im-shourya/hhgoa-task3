from enum import Enum
from dataclasses import dataclass
from typing import Optional
import logging

from src.evidence.models import EvidenceManifest
from src.evidence.hasher import hash_evidence
from src.blockchain.registry import EvidenceRegistryClient
from src.errors import BlockchainError

logger = logging.getLogger(__name__)


class ReverificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    TAMPERED = "TAMPERED"
    NOT_REGISTERED = "NOT_REGISTERED"
    INVALID = "INVALID"


@dataclass
class ReverificationResult:
    status: ReverificationStatus
    computed_hash: Optional[str] = None
    registered_hash: Optional[str] = None
    verified: bool = False
    message: str = ""
    timestamp: Optional[int] = None
    submitter: Optional[str] = None


class EvidenceReverificationService:
    def __init__(self, registry_client: EvidenceRegistryClient):
        self.registry_client = registry_client

    def verify(self, evidence: EvidenceManifest, registered_hash: Optional[str] = None) -> ReverificationResult:
        """
        Deterministically reverify an EvidenceManifest against the blockchain.
        
        Args:
            evidence (EvidenceManifest): The evidence to verify.
            registered_hash (Optional[str]): The originally registered SHA-256 fingerprint. 
                                             Must be provided to detect tampering accurately.
        """
        if not isinstance(evidence, EvidenceManifest):
            return ReverificationResult(
                status=ReverificationStatus.INVALID,
                message="Provided evidence is not a valid EvidenceManifest object."
            )
            
        # Step 1: Compute hash of the provided evidence
        try:
            computed_hash = hash_evidence(evidence)
        except Exception as e:
            logger.error(f"Failed to hash evidence deterministically: {e}")
            return ReverificationResult(
                status=ReverificationStatus.INVALID,
                message=f"Evidence hashing failed: {str(e)}"
            )

        # Step 2: Handle cases where the registered hash is unknown
        if not registered_hash:
            # We can only check if the computed hash itself happens to exist on chain.
            try:
                record = self.registry_client.verify_evidence(computed_hash)
            except BlockchainError as e:
                # IMPORTANT: Propagate blockchain errors rather than calling it TAMPERED/NOT_REGISTERED
                raise e

            if record["exists"]:
                return ReverificationResult(
                    status=ReverificationStatus.VERIFIED,
                    computed_hash=computed_hash,
                    registered_hash=computed_hash,
                    verified=True,
                    message="Computed hash is registered on the blockchain.",
                    timestamp=record["timestamp"],
                    submitter=record["submitter"]
                )
            else:
                return ReverificationResult(
                    status=ReverificationStatus.NOT_REGISTERED,
                    computed_hash=computed_hash,
                    registered_hash=None,
                    verified=False,
                    message="Computed hash not found on the blockchain."
                )

        # Step 3: We have a registered_hash, compare it securely
        try:
            # First, check if the registered_hash ACTUALLY exists on the blockchain
            record = self.registry_client.verify_evidence(registered_hash)
        except BlockchainError as e:
            raise e

        if not record["exists"]:
            return ReverificationResult(
                status=ReverificationStatus.NOT_REGISTERED,
                computed_hash=computed_hash,
                registered_hash=registered_hash,
                verified=False,
                message="The provided registered hash does not exist on the blockchain."
            )

        # The original hash is on the blockchain. Now compare to the computed hash.
        if computed_hash == registered_hash:
            return ReverificationResult(
                status=ReverificationStatus.VERIFIED,
                computed_hash=computed_hash,
                registered_hash=registered_hash,
                verified=True,
                message="Computed hash matches the blockchain-registered hash perfectly.",
                timestamp=record["timestamp"],
                submitter=record["submitter"]
            )
        else:
            return ReverificationResult(
                status=ReverificationStatus.TAMPERED,
                computed_hash=computed_hash,
                registered_hash=registered_hash,
                verified=False,
                message="Computed hash differs from the registered hash. Evidence was tampered with."
            )
