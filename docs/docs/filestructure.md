# File Structure

Recommended repository:

```text
hh-goa-task3/
│
├── README.md
├── LICENSE
├── .gitignore
├── env.example
├── requirements.txt
├── pyproject.toml
│
├── docs/
│   ├── techstack.md
│   ├── projectdetails.md
│   ├── filestructure.md
│   ├── architecture.md
│   ├── api.md
│   ├── data-model.md
│   ├── security.md
│   ├── testing.md
│   ├── demo.md
│   ├── deployment.md
│   ├── limitations.md
│   ├── acceptance-criteria.md
│   ├── troubleshooting.md
│   ├── decisions.md
│   └── ethics.md
│
├── app/
│   ├── __init__.py
│   ├── ui.py
│   ├── config.py
│   └── pipeline.py
│
├── src/
│   ├── __init__.py
│   ├── face.py
│   ├── reverse_search.py
│   ├── candidate.py
│   ├── evidence.py
│   ├── hashing.py
│   ├── blockchain.py
│   ├── models.py
│   └── utils.py
│
├── contracts/
│   ├── EvidenceRegistry.sol
│   └── abi/
│       └── EvidenceRegistry.json
│
├── scripts/
│   ├── deploy_contract.py
│   ├── search_test.py
│   ├── verify_test.py
│   └── tamper_demo.py
│
├── tests/
│   ├── test_face.py
│   ├── test_search.py
│   ├── test_evidence.py
│   ├── test_hashing.py
│   └── test_blockchain.py
│
├── data/
│   ├── input/
│   ├── candidates/
│   └── demo/
│
├── artifacts/
│   └── .gitkeep
│
└── .github/
    └── workflows/
        └── tests.yml
```

## Responsibilities

### `src/face.py`
- model initialization
- face detection
- alignment if required
- embedding generation
- similarity computation

### `src/reverse_search.py`
- provider interface
- provider implementation
- API response parsing
- normalization into common candidate format

### `src/candidate.py`
- URL validation
- image download
- candidate filtering
- face verification
- ranking

### `src/evidence.py`
- evidence manifest creation
- canonicalization
- metadata collection
- serialization

### `src/hashing.py`
- SHA-256
- optional perceptual hashes
- deterministic hash utilities

### `src/blockchain.py`
- RPC connection
- contract loading
- transaction construction
- signing
- submission
- receipt handling
- read-back verification

### `app/ui.py`
- Streamlit interface
- pipeline status
- result cards
- transaction details
- verification state

### `contracts/EvidenceRegistry.sol`
Minimal on-chain evidence registry.

### `scripts/`
Small command-line utilities for debugging and demonstration.

## Files that must never be committed

```text
.env
*.pem
*.key
wallet.json
seed.txt
private_key.txt
```

Also consider excluding large raw images and personal biometric data.
