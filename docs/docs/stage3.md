# Stage 3 — Blockchain Verification

## 1. Objective

Create a tamper-evident record of discovered evidence by hashing a canonical evidence representation and registering the fingerprint on a public testnet.

Recommended:
- Polygon Amoy
- Solidity
- web3.py
- SHA-256

## 2. Core Flow

```text
Matching post
  ↓
Evidence bundle
  ↓
Canonical manifest
  ↓
SHA-256
  ↓
32-byte fingerprint
  ↓
Smart contract
  ↓
Polygon Amoy transaction
  ↓
Transaction receipt
```

Verification:

```text
Current evidence
  ↓
Canonical manifest
  ↓
SHA-256
  ↓
Current fingerprint
  ↓
read blockchain record
  ↓
compare
  ↓
VERIFIED / TAMPERED
```

## 3. Why Not Store the Image On-Chain?

Images are large and expensive to store.

Instead:

```text
image
  ↓
SHA-256
  ↓
32 bytes
  ↓
blockchain
```

The original evidence can remain off-chain.

## 4. Evidence Manifest

Example:

```json
{
  "schema_version": "1.0",
  "source_url": "...",
  "source_platform": "...",
  "observed_at": "...",
  "post_text": "...",
  "image_sha256": "...",
  "face_similarity": 0.923,
  "search_provider": "..."
}
```

Do not include volatile or irrelevant values in the manifest if they prevent deterministic re-verification.

## 5. Canonicalization

Use deterministic JSON:

```python
canonical = json.dumps(
    evidence,
    sort_keys=True,
    separators=(",", ":")
)
```

Then:

```python
hash_value = hashlib.sha256(
    canonical.encode("utf-8")
).hexdigest()
```

The exact same canonical data produces the same fingerprint.

## 6. Image Hash

Optionally calculate:

```python
sha256_file("post_image.jpg")
```

Store the resulting image hash inside the manifest.

## 7. Smart Contract

Recommended minimal contract:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract EvidenceRegistry {
    struct Record {
        uint256 timestamp;
        address submitter;
    }

    mapping(bytes32 => Record) public records;

    event EvidenceRegistered(
        bytes32 indexed fingerprint,
        address indexed submitter,
        uint256 timestamp
    );

    function registerEvidence(bytes32 fingerprint) external {
        require(
            records[fingerprint].timestamp == 0,
            "Evidence already registered"
        );

        records[fingerprint] = Record({
            timestamp: block.timestamp,
            submitter: msg.sender
        });

        emit EvidenceRegistered(
            fingerprint,
            msg.sender,
            block.timestamp
        );
    }

    function verifyEvidence(bytes32 fingerprint)
        external
        view
        returns (
            bool exists,
            uint256 timestamp,
            address submitter
        )
    {
        Record memory record = records[fingerprint];

        return (
            record.timestamp != 0,
            record.timestamp,
            record.submitter
        );
    }
}
```

## 8. Deployment

Deploy once to Polygon Amoy.

Record:
- contract address
- deployment transaction
- network/chain ID
- ABI

Put public contract address in configuration/documentation.

Never publish the deployer's private key.

## 9. web3.py

Conceptual flow:

```python
w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=ABI
)
```

Convert SHA-256 hex to bytes:

```python
fingerprint_bytes = bytes.fromhex(
    fingerprint_hex
)
```

Submit:

```python
contract.functions.registerEvidence(
    fingerprint_bytes
)
```

Sign using a private key loaded from an environment variable.

## 10. Transaction Confirmation

Wait for the receipt.

Only report `CONFIRMED` if:
- receipt exists,
- receipt status indicates success.

Save:
- tx hash
- block number
- contract address
- network

## 11. Re-verification

Reconstruct the exact evidence manifest.

Calculate:

```text
local_hash
```

Read the contract using the same bytes32 fingerprint.

A stronger verification flow is:

1. calculate current local hash,
2. query the contract,
3. determine whether that exact hash exists,
4. retrieve timestamp/submitter,
5. display result.

## 12. Tamper Demonstration

Original:

```text
local = ABC
on-chain = ABC
```

Result:

`VERIFIED`

Modify evidence:

```text
local = XYZ
on-chain = ABC
```

Result:

`TAMPER DETECTED`

Restore:

```text
local = ABC
on-chain = ABC
```

Result:

`VERIFIED`

## 13. Important Meaning

The blockchain proves fingerprint continuity, not the truthfulness of the post.

It does not independently prove:
- that the social platform is authentic,
- that the account belongs to a specific person,
- that the person is legally identified,
- that the post content is true,
- that the image was originally created by the account.

## 14. Stage 3 Output

```json
{
  "network": "Polygon Amoy",
  "contract_address": "0x...",
  "fingerprint": "...",
  "transaction_hash": "0x...",
  "block_number": 123,
  "registered": true,
  "verified": true
}
```

## 15. Definition of Done

Stage 3 is complete when:
- evidence is deterministically hashed,
- hash is registered on Polygon Amoy,
- transaction is confirmed,
- transaction hash is shown,
- contract can be queried,
- re-verification returns `VERIFIED`,
- modified evidence returns `TAMPER DETECTED`.
