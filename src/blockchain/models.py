from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class BlockchainTransactionResult:
    """Result of a blockchain registration."""
    success: bool
    evidence_hash: str
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    chain_id: Optional[int] = None
    submitter: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "success"  # "success", "already_registered", "failed"
    error: Optional[str] = None
