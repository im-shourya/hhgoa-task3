import pytest
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress noisy loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings singleton between tests."""
    from src.config import reload_settings
    reload_settings()
    yield
    reload_settings()

@pytest.fixture(scope="module")
def w3():
    from eth_tester import EthereumTester
    from web3 import Web3
    from web3.providers.eth_tester import EthereumTesterProvider
    tester = EthereumTester()
    provider = EthereumTesterProvider(tester)
    web3_instance = Web3(provider)
    web3_instance.eth.default_account = web3_instance.eth.accounts[0]
    return web3_instance

@pytest.fixture(scope="module")
def evidence_registry(w3):
    import os
    import json
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abi_path = os.path.join(project_root, "build", "contracts_EvidenceRegistry_sol_EvidenceRegistry.abi")
    bin_path = os.path.join(project_root, "build", "contracts_EvidenceRegistry_sol_EvidenceRegistry.bin")
    
    with open(abi_path, "r") as f:
        abi = json.load(f)
    with open(bin_path, "r") as f:
        bytecode = f.read().strip()
        
    contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract_factory.constructor().transact()
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
    return contract