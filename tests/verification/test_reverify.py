import pytest
import dataclasses
from unittest.mock import MagicMock

from src.evidence.models import EvidenceManifest, EvidenceCandidate, EvidenceVerification, EvidenceProvenance
from src.evidence.hasher import hash_evidence
from src.blockchain.registry import EvidenceRegistryClient
from src.verification.reverify import EvidenceReverificationService, ReverificationStatus
from src.errors import BlockchainNetworkError


@pytest.fixture
def evidence():
    cand = EvidenceCandidate(page_url="A", image_url="B", domain="C", title="D")
    veri = EvidenceVerification(similarity="0.873421", decision="MATCH")
    prov = EvidenceProvenance(provider="prov", metadata={})
    return EvidenceManifest(schema_version="1.0", candidate=cand, verification=veri, provenance=prov)


@pytest.fixture(scope="module")
def registry_client(w3, evidence_registry):
    mock_client = MagicMock()
    mock_client.get_w3.return_value = w3
    mock_client.account = MagicMock()
    mock_client.account.address = w3.eth.default_account
    
    registry = EvidenceRegistryClient(client=mock_client, contract_address=evidence_registry.address)
    # mock _load_abi inside registry to return the deployed ABI
    registry.abi = evidence_registry.abi
    return registry


@pytest.fixture
def reverify_service(registry_client):
    return EvidenceReverificationService(registry_client)


def test_reverification_untampered(evidence, reverify_service, registry_client):
    # Test 1 — Untampered Evidence
    # Hash and register
    original_hash = hash_evidence(evidence)
    registry_client.register_evidence(original_hash)
    
    # Re-verify
    result = reverify_service.verify(evidence, registered_hash=original_hash)
    
    assert result.status == ReverificationStatus.VERIFIED
    assert result.verified is True
    assert result.computed_hash == original_hash
    assert result.registered_hash == original_hash


def test_reverification_single_field_tampering(evidence, reverify_service, registry_client):
    # Test 2 — Single-Field Tampering
    original_hash = hash_evidence(evidence)
    registry_client.register_evidence(original_hash)
    
    # Modify similarity
    tampered_veri = dataclasses.replace(evidence.verification, similarity="0.873422")
    tampered_evidence = dataclasses.replace(evidence, verification=tampered_veri)
    
    # Re-verify with tampered evidence against original hash
    result = reverify_service.verify(tampered_evidence, registered_hash=original_hash)
    
    assert result.status == ReverificationStatus.TAMPERED
    assert result.verified is False
    assert result.computed_hash != original_hash
    assert result.registered_hash == original_hash


def test_reverification_multiple_field_tampering(evidence, reverify_service, registry_client):
    # Test 3 — Multiple-Field Tampering
    original_hash = hash_evidence(evidence)
    registry_client.register_evidence(original_hash)
    
    # Modify multiple fields
    tampered_cand = dataclasses.replace(evidence.candidate, title="Tampered Title", domain="malicious.com")
    tampered_evidence = dataclasses.replace(evidence, candidate=tampered_cand)
    
    # Re-verify
    result = reverify_service.verify(tampered_evidence, registered_hash=original_hash)
    
    assert result.status == ReverificationStatus.TAMPERED
    assert result.verified is False
    assert result.computed_hash != original_hash


def test_reverification_unregistered_evidence(evidence, reverify_service):
    # Test 4 — Unregistered Evidence
    # Use unique evidence so it doesn't collide with other tests
    unique_cand = dataclasses.replace(evidence.candidate, title="Unregistered Unique")
    unique_evidence = dataclasses.replace(evidence, candidate=unique_cand)
    original_hash = hash_evidence(unique_evidence)
    # DO NOT register it
    
    # If passing registered_hash, it won't be on the blockchain
    result = reverify_service.verify(unique_evidence, registered_hash=original_hash)
    assert result.status == ReverificationStatus.NOT_REGISTERED
    assert result.verified is False
    
    # If not passing registered_hash, it checks computed_hash
    result2 = reverify_service.verify(unique_evidence)
    assert result2.status == ReverificationStatus.NOT_REGISTERED
    assert result2.verified is False


def test_reverification_invalid_evidence(reverify_service):
    # Test 5 — Invalid Evidence (e.g. causes hasher to crash)
    # We can pass an invalid object that cannot be hashed
    result = reverify_service.verify(None)
    assert result.status == ReverificationStatus.INVALID
    assert result.verified is False


def test_exact_hash_reproduction(evidence):
    # Test 6 — Exact Hash Reproduction
    # The hash computed by reverify_service should exactly match Phase 4 hash_evidence
    expected = hash_evidence(evidence)
    # The verify method computes this internally
    # Let's mock registry_client to avoid doing actual network calls
    mock_registry = MagicMock()
    mock_registry.verify_evidence.return_value = {"exists": True, "timestamp": 123, "submitter": "0xABC"}
    svc = EvidenceReverificationService(mock_registry)
    
    result = svc.verify(evidence)
    assert result.computed_hash == expected


def test_blockchain_integration(evidence, registry_client, reverify_service):
    # Test 7 — Blockchain Integration (EthereumTesterProvider)
    # Already implicitly tested in Test 1, but let's test the workflow explicitly
    # Avoid duplicate from Test 1 by tweaking a field
    tampered_cand = dataclasses.replace(evidence.candidate, title="Unique Test 7")
    ev2 = dataclasses.replace(evidence, candidate=tampered_cand)
    h2 = hash_evidence(ev2)
    
    # 1. verify (should be not registered)
    res1 = reverify_service.verify(ev2)
    assert res1.status == ReverificationStatus.NOT_REGISTERED
    
    # 2. register
    registry_client.register_evidence(h2)
    
    # 3. verify (should be registered)
    res2 = reverify_service.verify(ev2)
    assert res2.status == ReverificationStatus.VERIFIED


def test_tamper_after_registration(evidence, registry_client, reverify_service):
    # Test 8 — Tamper After Blockchain Registration
    h = hash_evidence(evidence)
    # registry_client.register_evidence(h) # Already registered in Test 1
    
    # Modify evidence
    tampered_prov = dataclasses.replace(evidence.provenance, provider="hacker_api")
    tampered_evidence = dataclasses.replace(evidence, provenance=tampered_prov)
    
    # Calculate new hash
    new_hash = hash_evidence(tampered_evidence)
    
    # Re-verify (must provide the original hash)
    res = reverify_service.verify(tampered_evidence, registered_hash=h)
    
    assert res.status == ReverificationStatus.TAMPERED
    assert res.computed_hash == new_hash


def test_missing_blockchain_record(reverify_service):
    # Test 9 — Missing Blockchain Record
    dummy_hex = "f9" * 32
    
    # Mock registry returning exists = False
    mock_registry = MagicMock()
    mock_registry.verify_evidence.return_value = {"exists": False}
    svc = EvidenceReverificationService(mock_registry)
    
    # Dummy evidence
    cand = EvidenceCandidate(page_url="A", image_url="B", domain="C", title="D")
    veri = EvidenceVerification(similarity="0", decision="MATCH")
    prov = EvidenceProvenance(provider="prov", metadata={})
    ev = EvidenceManifest(schema_version="1.0", candidate=cand, verification=veri, provenance=prov)
    
    res = svc.verify(ev, registered_hash=dummy_hex)
    assert res.status == ReverificationStatus.NOT_REGISTERED


def test_blockchain_error_handling(evidence):
    # Test 10 — Blockchain Error Handling
    mock_registry = MagicMock()
    mock_registry.verify_evidence.side_effect = BlockchainNetworkError("RPC offline")
    svc = EvidenceReverificationService(mock_registry)
    
    with pytest.raises(BlockchainNetworkError, match="RPC offline"):
        svc.verify(evidence)
