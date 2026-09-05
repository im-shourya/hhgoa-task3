import pytest
import os
import json
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider

@pytest.fixture(scope="module")
def w3():
    return Web3(EthereumTesterProvider())

@pytest.fixture(scope="module")
def contract_interface():
    build_dir = os.path.join(os.path.dirname(__file__), "..", "..", "build")
    abi_path = os.path.join(build_dir, "contracts_EvidenceRegistry_sol_EvidenceRegistry.abi")
    bin_path = os.path.join(build_dir, "contracts_EvidenceRegistry_sol_EvidenceRegistry.bin")
    
    if not os.path.exists(abi_path) or not os.path.exists(bin_path):
        pytest.skip("Contract build files not found. Run compile_contract.py first.")
        
    with open(abi_path, "r") as f:
        abi = json.load(f)
    with open(bin_path, "r") as f:
        bytecode = f.read().strip()
        
    return abi, bytecode

@pytest.fixture
def evidence_registry(w3, contract_interface):
    abi, bytecode = contract_interface
    # Get the testing accounts
    w3.eth.default_account = w3.eth.accounts[0]
    
    EvidenceRegistry = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = EvidenceRegistry.constructor().transact()
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=abi
    )

def test_deploy(evidence_registry):
    assert evidence_registry.address is not None

def test_store_and_retrieve_evidence(evidence_registry, w3):
    # Dummy SHA-256 hash representing Phase 4 output
    dummy_hex = "a3f8" * 16 # 64 chars
    fingerprint = bytes.fromhex(dummy_hex)
    
    tx_hash = evidence_registry.functions.registerEvidence(fingerprint).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Check existence
    assert evidence_registry.functions.evidenceExists(fingerprint).call() is True
    
    # Retrieve record
    exists, timestamp, submitter = evidence_registry.functions.getEvidence(fingerprint).call()
    
    assert exists is True
    assert timestamp > 0
    assert submitter == w3.eth.default_account

def test_duplicate_evidence_rejected(evidence_registry, w3):
    dummy_hex = "b4f8" * 16 
    fingerprint = bytes.fromhex(dummy_hex)
    
    tx_hash = evidence_registry.functions.registerEvidence(fingerprint).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Attempting to register the exact same fingerprint should fail
    with pytest.raises(Exception):
        evidence_registry.functions.registerEvidence(fingerprint).transact()

def test_zero_hash_rejected(evidence_registry):
    fingerprint = bytes.fromhex("00" * 32)
    
    with pytest.raises(Exception):
        evidence_registry.functions.registerEvidence(fingerprint).transact()

def test_immutability(evidence_registry, w3):
    dummy_hex = "c5f8" * 16 
    fingerprint = bytes.fromhex(dummy_hex)
    
    tx_hash = evidence_registry.functions.registerEvidence(fingerprint).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Re-registering fails, ensuring the original timestamp and submitter are immutable
    with pytest.raises(Exception):
        evidence_registry.functions.registerEvidence(fingerprint).transact({'from': w3.eth.accounts[1]})
        
    _, _, submitter = evidence_registry.functions.getEvidence(fingerprint).call()
    assert submitter == w3.eth.default_account

def test_unregistered_evidence(evidence_registry):
    dummy_hex = "d6f8" * 16
    fingerprint = bytes.fromhex(dummy_hex)
    
    exists = evidence_registry.functions.evidenceExists(fingerprint).call()
    assert exists is False
    
    ex, ts, sub = evidence_registry.functions.getEvidence(fingerprint).call()
    assert ex is False
    assert ts == 0
