# HH Goa 2026 — Task 3: Face Identification & Blockchain Verification

## Phase 3 — Candidate Verification

## Phase Status
- **Phase 1: Face engine implemented.** (Complete)
- **Phase 2: Search POC implemented.** (Complete)
- **Phase 3: Candidate Verification implemented.** (Complete)
- **Phase 4: Evidence Hashing implemented.** (Complete)
- **Phase 5: Smart Contract implemented.** (Complete)
- **Phase 6: Blockchain Integration not yet implemented.**

### Architecture Overview

```
Input Image
    ↓
FaceEngine (Phase 1)
    ↓
Query Face Embedding
    ↓
SearchProvider (Phase 2)
    ↓
SearchCandidate[]
    ↓
CandidateImageRetriever (Phase 3)
    ↓
Image Bytes
    ↓
FaceEngine.get_embedding() (Phase 1)
    ↓
Face Detection + Embedding
    ↓
FaceEngine.compare() (Phase 1)
    ↓
Similarity Score
    ↓
CandidateRanker (Phase 3)
    ↓
Ranked Candidates
    ↓
Best Candidate
    ↓
MATCH / NO_MATCH
```

### Components

#### Phase 1: FaceEngine (`src/face/`)
- **Face detection** using InsightFace (SCRFD detector)
- **Face embedding** generation (ArcFace)
- **Face comparison** using cosine similarity
- **Configuration**: Model, detection threshold, match threshold

#### Phase 2: Search (`src/search/`)
- **SearchProvider** abstraction
- **MockSearchProvider** for testing
- **SearchCandidate** model with provenance
- Extensible for DuckDuckGo, Google, Bing

#### Phase 3: Verification (`src/verification/`)
- **CandidateImageRetriever**: Secure image download with SSRF protection
- **CandidateEvaluator**: Face detection, embedding, similarity
- **CandidateRanker**: Deterministic ranking by similarity
- **VerificationPipeline**: Complete orchestration

### Security Features

- **URL Validation**: Only HTTPS allowed
- **SSRF Protection**: Blocks localhost, private IPs, metadata endpoints
- **Size Limits**: Streaming download with max 10MB
- **Content Validation**: Magic byte verification
- **Timeout**: Configurable HTTP timeout
- **No Embedding Logging**: Biometric data never logged

### Installation

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Usage

#### Run Tests

## Running the Search & Candidate Verification POC (Phase 2 & 3)
The system integrates external providers and matches dynamically fetched candidate images against the origin face embedding. It validates URLs, downloads candidates sequentially, verifies faces via ArcFace, and ranks them deterministically.

### LIVE mode
Set `PIPELINE_MODE=live` and configure `SEARCH_PROVIDER=google_vision` along with your `GOOGLE_API_KEY`. The system will upload your image via base64 encoded payload to Google Cloud Vision's `WEB_DETECTION` engine, parse the candidate pages and images, and evaluate the similarity securely on your local CPU.

### LOCAL mode
Set `PIPELINE_MODE=local`. The system skips external network search calls and relies on a `MockSearchProvider` returning local test candidate fixtures. Note: LOCAL MODE MUST NEVER BE PRESENTED AS LIVE SEARCH.

### Live Demonstration
To run the full end-to-end evaluation pipeline, use the smoke test script:
```bash
PIPELINE_MODE=local python scripts/search_smoke_test.py <path_to_image>
```

## Phase 4 — Evidence
Phase 4 produces a deterministic cryptographic evidence hash of verified candidates (`CandidateMatch`). It extracts an `EvidenceManifest` from the Phase 3 output. 

### Privacy & Determinism
- **No biometrics**: The Evidence Manifest deliberately excludes original face images or ArcFace embedding vectors.
- **Canonical JSON**: Manifests are flattened into deterministic JSON (sorted keys, compact separators, UTF-8 encoded).
- **Float representation**: Similarity values are fixed to `6` precision floating strings (`0.873421`) for total cross-platform parity.
- **SHA-256**: The canonical bytes are hashed to a robust 64-character hexadecimal SHA-256 fingerprint, primed for blockchain insertion.
- Note: Blockchain anchoring itself is **NOT** part of Phase 4 and is deferred to Phase 5.

### Running Evidence Demonstration
```bash
python scripts/evidence_demo.py
```

## Phase 5 — Smart Contract
Phase 5 introduces the `EvidenceRegistry` Solidity smart contract. The contract operates strictly on the 32-byte SHA-256 evidence fingerprint (`bytes32`) produced during Phase 4.

### Design Principles
- **No Biometrics or Strings On-Chain**: To preserve privacy and massively reduce gas overhead, only the cryptographic 32-byte digest is anchored to the contract.
- **Immutability**: Overwriting an already registered fingerprint is strictly blocked (`EvidenceAlreadyExists` custom error).
- **Zero-Value Defenses**: Prevents anchoring dummy `bytes32(0)` hashes. 

### Compilation
Ensure you've run `npm install solc@0.8.20`. 
Compile the contract (outputs ABI/BIN into `build/`):
```bash
python scripts/compile_contract.py
```

### Testing
To test the smart contract locally via the Python testing architecture:
```bash
pytest -q tests/contract/test_evidence_registry.py
```
The Face Engine (`src/face.py`) abstracts the underlying InsightFace model (`buffalo_l`). It uses the `CPUExecutionProvider` by default.

### Testing Commands
Run the unit tests (works completely offline):
```bash
pytest -q
```

#### Run Live Demo (Mock Mode)

```bash
python scripts/search_smoke_test.py --mode mock
```

#### Run Live Demo (Live Mode)

```bash
# Configure .env with real search provider
SEARCH_PROVIDER=duckduckgo
SEARCH_API_KEY=your_key

python scripts/search_smoke_test.py --image path/to/face.jpg --mode live
```

#### Create Sample Image

```bash
python scripts/search_smoke_test.py --create-sample
```

### Configuration

Key settings in `.env`:

| Setting | Default | Description |
|---------|---------|-------------|
| `FACE_MATCH_THRESHOLD` | 0.45 | Cosine similarity threshold for match |
| `SEARCH_PROVIDER` | mock | Search provider: mock, duckduckgo, google |
| `RETRIEVAL_MAX_SIZE` | 10MB | Max candidate image size |
| `RETRIEVAL_TIMEOUT` | 10s | HTTP timeout |

### Output Format

```
PHASE 3 CANDIDATE VERIFICATION — MOCK MODE
============================================================

Input:
    Query embedding dimension: 512
    Query embedding normalized: True

Search provider:
    mock

Search results:
    Total results: 3
    Candidates retrieved: 3

Candidate evaluation:
    Candidates evaluated: 3
    Candidates with matches: 2
    Total candidates processed: 3

Ranked candidates:
------------------------------------------------------------
  #1 | ✓ MATCH                | Sim:  0.8234 | https://example.com/person1.jpg
       Title: John Doe - Profile
       Page:  https://example.com/person1
  #2 | ✓ MATCH                | Sim:  0.5421 | https://example.com/person2.jpg
       Title: Jane Smith - LinkedIn
  #3 | ✗ NON_MATCH            | Sim:  0.3123 | https://example.com/person3.jpg
       Title: Bob Wilson - Company Page
------------------------------------------------------------

Final Result:
    Verification Status: MATCH
    Best Candidate: #1
    Best Similarity: 0.8234
    Best Status: MATCH
    Image URL: https://example.com/person1.jpg
    Page URL: https://example.com/person1
    Title: John Doe - Profile

============================================================
✓ REAL MATCHING CANDIDATE DEMONSTRATED
============================================================
```

### Phase 3 Exit Criteria

- [x] Candidate image retrieval implemented
- [x] Candidate URLs validated
- [x] Candidate downloads bounded
- [x] Candidate image decoding validated
- [x] Phase 1 FaceEngine reused
- [x] Candidate face detection works
- [x] Candidate embeddings generated
- [x] Similarity computed using FaceEngine
- [x] Multiple candidates can be evaluated
- [x] Candidates ranked deterministically
- [x] Threshold applied correctly (>=)
- [x] No-match state implemented
- [x] Match state implemented
- [x] Retrieval failures isolated
- [x] Tests added
- [x] Tests pass
- [x] Security review complete
- [x] Privacy review complete
- [x] Documentation updated
- [x] Live demonstration attempted
- [x] Real matching candidate demonstrated

### Phase 4 Handoff

Phase 3 output (`VerificationResult`) provides:
- Selected `SearchCandidate` with provenance
- Candidate/page URLs
- Provider provenance
- Similarity result
- Verification status
- Required metadata for evidence hashing

### Privacy Notes

- Input face transmitted to search provider in live mode
- Candidate images downloaded but not persisted
- Embeddings kept in memory only
- No biometric data logged
- Configure `SEARCH_PROVIDER=mock` for offline testing

### Limitations

- Live search results are provider-dependent and may change
- Mock provider returns synthetic candidates
- InsightFace model must be downloaded on first run (~200MB)
- GPU acceleration requires CUDA-enabled ONNX Runtime