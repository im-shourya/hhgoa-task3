import logging
from web3 import Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder
from eth_account import Account

from src.config import get_settings
from src.errors import BlockchainNetworkError

logger = logging.getLogger(__name__)

class BlockchainClient:
    def __init__(self, rpc_url: str = None, private_key: str = None, expected_chain_id: int = None):
        settings = get_settings()
        self.rpc_url = rpc_url or settings.blockchain_rpc_url
        self.private_key = private_key or settings.blockchain_private_key
        self.expected_chain_id = expected_chain_id or settings.blockchain_chain_id
        
        if not self.rpc_url:
            raise BlockchainNetworkError("Blockchain RPC URL is required when blockchain is enabled")
            
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        if not self.w3.is_connected():
            raise BlockchainNetworkError(f"Failed to connect to blockchain node at {self.rpc_url}")
            
        actual_chain_id = self.w3.eth.chain_id
        if actual_chain_id != self.expected_chain_id:
            raise BlockchainNetworkError(f"Chain ID mismatch. Expected {self.expected_chain_id}, got {actual_chain_id}")
            
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            self.w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(self.account), layer=0)
            self.w3.eth.default_account = self.account.address
            logger.info(f"Initialized BlockchainClient on chain {actual_chain_id} with account {self.account.address}")
        else:
            self.account = None
            logger.info(f"Initialized read-only BlockchainClient on chain {actual_chain_id}")
            
    def get_w3(self) -> Web3:
        return self.w3
