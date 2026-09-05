import pytest
from unittest.mock import patch, MagicMock

from src.blockchain.client import BlockchainClient
from src.blockchain.registry import EvidenceRegistryClient
from src.errors import BlockchainError, BlockchainNetworkError

# Use fixtures from tests.contract.conftest if possible, or create a mock w3 setup
def test_blockchain_client_initialization_fails_without_url():
    with pytest.raises(BlockchainNetworkError, match="Blockchain RPC URL is required"):
        BlockchainClient(rpc_url=None)

@patch('src.blockchain.client.Web3')
def test_blockchain_client_initialization_fails_not_connected(mock_web3_class):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = False
    mock_web3_class.return_value = mock_w3
    
    with pytest.raises(BlockchainNetworkError, match="Failed to connect to blockchain node"):
        BlockchainClient(rpc_url="http://fake", expected_chain_id=1337)

@patch('src.blockchain.client.Web3')
def test_blockchain_client_initialization_chain_mismatch(mock_web3_class):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.chain_id = 9999
    mock_web3_class.return_value = mock_w3
    
    with pytest.raises(BlockchainNetworkError, match="Chain ID mismatch. Expected 1337, got 9999"):
        BlockchainClient(rpc_url="http://fake", expected_chain_id=1337)

@patch('src.blockchain.client.Web3')
def test_blockchain_client_initialization_success(mock_web3_class):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.chain_id = 1337
    mock_web3_class.return_value = mock_w3
    
    client = BlockchainClient(rpc_url="http://fake", expected_chain_id=1337)
    assert client.get_w3() == mock_w3

def test_registry_client_requires_address():
    mock_client = MagicMock()
    
    with pytest.raises(BlockchainError, match="EvidenceRegistry contract address is required"):
        with patch('src.blockchain.registry.get_settings') as mock_settings:
            settings_mock = MagicMock()
            settings_mock.blockchain_contract_address = None
            settings_mock.blockchain_tx_timeout = 120
            mock_settings.return_value = settings_mock
            
            EvidenceRegistryClient(client=mock_client)

def test_evidence_registry_end_to_end(w3, evidence_registry):
    # We can use the real tester w3 and deployed contract!
    
    # Mock the client
    mock_client = MagicMock()
    mock_client.get_w3.return_value = w3
    mock_client.account = MagicMock()
    mock_client.account.address = w3.eth.default_account
    
    # Init registry client
    # Note: we need to patch _load_abi to return the actual ABI since we are using eth-tester
    with patch.object(EvidenceRegistryClient, '_load_abi', return_value=evidence_registry.abi):
        registry_client = EvidenceRegistryClient(client=mock_client, contract_address=evidence_registry.address)
        
        # 1. Verify unregistered evidence
        dummy_hex = "f9" * 32
        result = registry_client.verify_evidence(dummy_hex)
        assert result["exists"] is False
        assert result["timestamp"] == 0
        assert result["submitter"] is None
        
        # 2. Register evidence
        tx_res = registry_client.register_evidence(dummy_hex)
        assert tx_res.success is True
        assert tx_res.status == "success"
        assert tx_res.evidence_hash == dummy_hex
        assert tx_res.transaction_hash is not None
        
        # 3. Verify registered evidence
        result2 = registry_client.verify_evidence(dummy_hex)
        assert result2["exists"] is True
        assert result2["timestamp"] > 0
        assert result2["submitter"] == w3.eth.default_account
        
        # 4. Register duplicate evidence
        tx_res2 = registry_client.register_evidence(dummy_hex)
        assert tx_res2.success is True
        assert tx_res2.status == "already_registered"
