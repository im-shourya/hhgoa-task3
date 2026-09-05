import sys
import os

# Add the project root to sys.path so we can import src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

import dataclasses
from src.evidence.models import EvidenceManifest, EvidenceCandidate, EvidenceVerification, EvidenceProvenance
from src.evidence.hasher import hash_evidence
from src.verification.reverify import EvidenceReverificationService
from src.blockchain.client import BlockchainClient
from src.blockchain.registry import EvidenceRegistryClient

def main():
    print("================================================")
    print("PHASE 7 — RE-VERIFICATION DEMO")
    print("================================================\n")
    
    # Check if Polygon Amoy is properly configured, else use offline mock
    import dotenv
    dotenv.load_dotenv()
    
    rpc_url = os.getenv("BLOCKCHAIN_RPC_URL")
    private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
    contract_address = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS")
    
    # Try to initialize live connection if credentials exist, otherwise mock
    use_live = bool(rpc_url and private_key and contract_address)
    
    if use_live:
        print("[!] Using Live Polygon Amoy Blockchain credentials.")
        try:
            client = BlockchainClient()
            registry_client = EvidenceRegistryClient(client)
        except Exception as e:
            print(f"[!] Failed to connect to live network: {e}")
            print("[!] Falling back to mock offline setup.\n")
            use_live = False
    
    if not use_live:
        print("[!] Using Mock Offline EthereumTester for demonstration.")
        from eth_tester import EthereumTester
        from web3 import Web3
        from web3.providers.eth_tester import EthereumTesterProvider
        
        tester = EthereumTester()
        provider = EthereumTesterProvider(tester)
        w3 = Web3(provider)
        w3.eth.default_account = w3.eth.accounts[0]
        
        # Deploy contract dynamically for the mock
        import json
        abi_path = os.path.join(project_root, "build", "contracts_EvidenceRegistry_sol_EvidenceRegistry.abi")
        bin_path = os.path.join(project_root, "build", "contracts_EvidenceRegistry_sol_EvidenceRegistry.bin")
        
        with open(abi_path, "r") as f:
            abi = json.load(f)
        with open(bin_path, "r") as f:
            bytecode = f.read().strip()
            
        contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = contract_factory.constructor().transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        
        class MockClient:
            def __init__(self, w3):
                self.w3 = w3
                self.account = type('MockAccount', (), {'address': w3.eth.default_account})()
            def get_w3(self): return self.w3
            
        from unittest.mock import patch
        mock_blockchain_client = MockClient(w3)
        
        with patch.object(EvidenceRegistryClient, '_load_abi', return_value=abi):
            registry_client = EvidenceRegistryClient(client=mock_blockchain_client, contract_address=contract_address)

    # Initialize Service
    reverify_service = EvidenceReverificationService(registry_client)

    # 1. Original Evidence
    cand = EvidenceCandidate(page_url="https://x.com/user/1", image_url="https://x.com/img.jpg", domain="x.com", title="Found Match")
    veri = EvidenceVerification(similarity="0.873421", decision="MATCH")
    prov = EvidenceProvenance(provider="google_vision", metadata={"provider_result_id": "gv_99"})
    original_evidence = EvidenceManifest(schema_version="1.0", candidate=cand, verification=veri, provenance=prov)
    
    original_hash = hash_evidence(original_evidence)
    
    print("[1] Original Evidence Created")
    print(f"Hash: {original_hash}\n")
    
    # 2. Register
    print("[2] Register / Locate Blockchain Record")
    tx_res = registry_client.register_evidence(original_hash)
    if tx_res.status == "already_registered":
        print("Status: REGISTERED (Already Existed on-chain)\n")
    else:
        print(f"Status: REGISTERED (Tx Hash: {tx_res.transaction_hash})\n")
    
    # 3. Re-verify Original
    print("[3] Re-verify Original Evidence")
    result_valid = reverify_service.verify(original_evidence, registered_hash=original_hash)
    print(f"Result: {result_valid.status.value}\n")
    
    # 4. Tamper Evidence
    print("[4] Tampering Evidence")
    print("Changed:")
    print("similarity: 0.873421 → 0.873422\n")
    
    tampered_veri = dataclasses.replace(original_evidence.verification, similarity="0.873422")
    tampered_evidence = dataclasses.replace(original_evidence, verification=tampered_veri)
    
    # 5. Recalculate Hash
    tampered_hash = hash_evidence(tampered_evidence)
    print("[5] Recalculate Hash")
    print(f"New Hash: {tampered_hash}\n")
    
    # 6. Re-verify Tampered
    print("[6] Re-verify Tampered Evidence (Against original registered hash)")
    result_tampered = reverify_service.verify(tampered_evidence, registered_hash=original_hash)
    print(f"Result: {result_tampered.status.value}")
    print(f"Reason: {result_tampered.message}\n")
    
    print("================================================")
    print("DEMO COMPLETE")
    print("================================================\n")

if __name__ == "__main__":
    main()
