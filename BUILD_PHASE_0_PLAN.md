# HH Goa 2026 Task 3

# Build Phase 0 — Execution Plan

## 1. Executive Summary
This execution plan defines the end-to-end architecture and implementation roadmap for HH Goa 2026 Task 3. The objective is to build a demonstrative pipeline that takes a user-provided face image, generates a biometric embedding, performs a genuine reverse-image web search, dynamically retrieves and verifies candidate matches, and securely registers a cryptographic fingerprint of the evidence onto the Polygon Amoy blockchain. 

## 2. Competition Requirements
1. **Detect and encode a face** from an input image using InsightFace.
2. **Perform a genuine web/social-media search** using that image (no hardcoded targets).
3. **Dynamically discover** at least one real matching post by evaluating candidate images.
4. **Independently verify** the candidate face against the source embedding.
5. **Upload the discovered evidence's fingerprint** to the Polygon Amoy testnet blockchain.
6. **Recalculate and verify** the fingerprint against the blockchain record (tamper-evident demonstration).
7. **Provide the complete source** in GitHub.
8. **Provide a screen recording** demonstrating the complete pipeline.

## 3. Documentation Analysis
The following documentation files were discovered in `./md/` and analyzed:
- `README.md`, `projectdetails.md`: Defines overall pipeline, scope, and principles.
- `acceptance-criteria.md`, `features.md`, `task.md`: Defines functionality and mandatory criteria.
- `architecture.md`, `filestructure.md`, `techstack.md`, `api.md`, `data-model.md`: Establishes the technical foundation, separation of concerns, and toolchain.
- `stage1.md`, `stage2.md`, `stage3.md`: Detailed stage-by-stage implementation specs.
- `security.md`, `privacy.md`, `ethics.md`: Outlines threat models, biometric data protection, and responsible use.
- `blockchain.md` / `EvidenceRegistry`: Minimal smart contract requirements.
- `demo.md`, `testing.md`, `troubleshooting.md`, `local-test-mode.md`: Demo recording scripts, test strategies, and fail-safes.
- `buildphase.md`, `plan.md`, `change-log.md`, `submission-checklist.md`, `reproducibility.md`, `risk-register.md`: Project management and phase definitions.

*Note: Some documents mentioned in the project outline (e.g., `AGENTS.md`, `requirements-traceability.md`) were not present in the package, but all existing documentation covers the requisite domains entirely.*

## 4. Requirement Traceability

| ID | Description | Source | Priority | Component | AC |
|---|---|---|---|---|---|
| FND-1 | Python 3.11+ environment and dependencies | `techstack.md` | High | Core | App launches |
| FACE-1 | Detect face and generate ArcFace embedding | `stage1.md` | High | `src/face.py` | Embedding generated |
| SEARCH-1 | Genuine dynamic reverse-image search via Provider | `stage2.md` | High | `src/reverse_search.py`| Valid candidates returned |
| MATCH-1 | Retrieve candidates and detect/embed faces | `stage2.md` | High | `src/candidate.py` | Face similarity computed |
| EVD-1 | Create canonical JSON manifest & SHA-256 | `data-model.md`| High | `src/evidence.py` | Hash is deterministic |
| BC-1 | Register fingerprint to Polygon Amoy | `stage3.md` | High | `src/blockchain.py`| Tx confirmed on-chain |
| BC-2 | Read back fingerprint and compare | `stage3.md` | High | `src/blockchain.py`| Verification succeeds |
| SEC-1 | Hide all secrets (API keys, wallets) | `security.md` | High | Config | No secrets in git |
| PRIV-1 | Do not store embeddings on-chain | `privacy.md` | High | Pipeline | Only hashes on-chain |

## 5. Conflicts and Ambiguities
- **Conflicts**: No explicit conflicts exist among the provided documents.
- **Ambiguities / Decisions Required**: 
  - **DECISION REQUIRED: Search Provider**. The exact reverse-image-search provider is not finalized (only `TinEyeSearcher` is given as an example). 
    - *Options*: TinEye API, Bing Visual Search, SerpApi Google Reverse Image.
    - *Recommendation*: Use SerpApi (Google Lens/Reverse Image Search) or Bing Visual Search API, as they offer generous free tiers and JSON responses containing source URLs and image links.
    - *Impact*: Pipeline cannot progress to Stage 2 without an API key and provider adapter.
  - **DECISION REQUIRED: Threshold**. The face match threshold is variable.
    - *Recommendation*: Expose `FACE_MATCH_THRESHOLD` in `.env` and default to `0.45` (standard for ArcFace cosine similarity), labeled "Experimental threshold" in the UI.

## 6. Final Architecture
```text
USER (Input Image)
 ↓
UI (Streamlit `app/ui.py`)
 ↓
Pipeline Orchestrator (`app/pipeline.py`)
 ├── Input Validation
 ├── Face Engine (`src/face.py` - InsightFace/ArcFace)
 ├── Search Adapter (`src/reverse_search.py` - External API)
 ├── Candidate Processor (`src/candidate.py` - Image retrieval & Match)
 ├── Evidence Builder (`src/evidence.py` - JSON Canonicalization)
 ├── Hash Service (`src/hashing.py` - SHA-256)
 └── Blockchain Client (`src/blockchain.py` - Web3.py)
          ↓
       Smart Contract (`contracts/EvidenceRegistry.sol` on Polygon Amoy)
```

## 7. Technology Decisions
- **Python 3.11+**: Provides robust ML and web3 ecosystem support.
- **InsightFace / ArcFace / ONNX**: Standard, high-accuracy face recognition models. Runs fast locally.
- **OpenCV / Pillow / NumPy**: Reliable image and vector manipulation tools.
- **Reverse Image Search API**: Avoids scraping limits. (Provider TBD, abstracted).
- **Streamlit**: Enables rapid, presentable UI development suitable for Hackathons.
- **Web3.py / Solidity**: Industry standard for EVM interaction.
- **Polygon Amoy**: Recommended testnet; fast block times and free testnet gas.

## 8. Face Engine Plan
- **Model**: InsightFace with `buffalo_l` (or equivalent ONNX model).
- **Execution**: `cv2.imread()` -> InsightFace `app.get(image)`.
- **Selection**: Require exactly one face for source; if multiple, reject or prompt user.
- **Embedding**: Extract the `embedding` attribute, normalize it.
- **Similarity**: Cosine similarity via `np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))`.

## 9. Search Strategy
- **Adapter Pattern**: Implement a base `ReverseImageSearcher` class.
- **Inputs**: Source image bytes/path.
- **Outputs**: List of normalized candidate objects `{"url", "image_url", "title", "source_domain", "provider"}`.
- **Provider constraint**: Must return source URLs and image URLs. Do NOT hardcode targets.

## 10. Candidate Matching Strategy
1. Deduplicate candidate URLs.
2. Download candidate images (skip failures/timeouts).
3. Pass images to Face Engine.
4. Compare all detected faces in a candidate against the source embedding.
5. Take the highest similarity score for the candidate.
6. Rank all candidates and select the best one that exceeds `FACE_MATCH_THRESHOLD`.

## 11. Evidence Model
```json
{
  "schema_version": "1.0",
  "source_url": "https://example.com/social-post",
  "source_platform": "example.com",
  "observed_at": "2026-09-01T11:22:24Z",
  "post_text": "Optional extracted text",
  "page_title": "Post Title",
  "image_sha256": "abcdef1234567890...",
  "face_similarity": 0.923,
  "search_provider": "BingVisualSearch"
}
```

## 12. Hashing Model
- **Canonicalization**: Convert Evidence Model dict to JSON using `json.dumps(data, sort_keys=True, separators=(',', ':'))`. Encode to `utf-8`.
- **Hashing**: `hashlib.sha256(canonical_bytes).hexdigest()`.
- **Blockchain Ready**: Convert 64-char hex to 32-byte array (`bytes32` in Solidity).

## 13. Blockchain Architecture
- **Network**: Polygon Amoy Testnet.
- **RPC & Wallet**: Managed via `.env` (`POLYGON_RPC_URL`, `PRIVATE_KEY`, `WALLET_ADDRESS`).
- **Client**: `web3.py`.
- **Transaction**: Construct `registerEvidence` call, sign with `PRIVATE_KEY`, send raw transaction, wait for receipt.

## 14. Smart Contract Specification
- **Contract Name**: `EvidenceRegistry`
- **Storage**: `mapping(bytes32 => Record) public records;`
- **Struct Record**: `{ uint256 timestamp; address submitter; }`
- **Functions**:
  - `registerEvidence(bytes32 fingerprint)`: Reverts if already registered. Saves timestamp & sender. Emits `EvidenceRegistered`.
  - `verifyEvidence(bytes32 fingerprint)`: Returns `(bool exists, uint256 timestamp, address submitter)`.

## 15. Verification Model
- **VERIFIED**: Local computed hash exactly matches an existing record on-chain.
- **TAMPER DETECTED / FINGERPRINT NOT FOUND**: Local computed hash does not exist on-chain.
- **Tamper Demo**: UI button to flip a bit/string in the local evidence, recalculate, and show mismatch, then restore.

## 16. Security Threat Model
- **API/Private Key Leakage**: High impact, mitigated by strict `.gitignore` and `.env` separation.
- **SSRF / Malicious Images**: Medium impact, mitigated by bounded timeouts and `Pillow`/`OpenCV` safe decoding.
- **False Matches**: Medium impact, mitigated by labeling threshold as "Experimental" and preventing automated identity claims.

## 17. Privacy Model
- **Biometric lifecycle**: Image -> Memory -> Embedding -> Similarity -> Memory clear.
- **On-chain**: Only the SHA-256 fingerprint goes on-chain. Embeddings and raw images are strictly kept off-chain.

## 18. Local Test Mode
- Uses mock `ReverseImageSearcher` returning local fixture URLs/JSON.
- Uses mock `EvidenceRegistry` (local dictionary).
- Visibly displays: **LOCAL TEST MODE — NOT LIVE SEARCH**.

## 19. Live Mode
- Uses real search API and Polygon Amoy testnet.
- Visibly displays: **LIVE SEARCH**.

## 20. Repository Structure
Matches standard Python architecture requested in `filestructure.md`:
```
hh-goa-task3/
├── app/ -> ui.py, config.py, pipeline.py
├── src/ -> face.py, reverse_search.py, candidate.py, evidence.py, hashing.py, blockchain.py
├── contracts/ -> EvidenceRegistry.sol
├── tests/
├── scripts/
├── .env.example
├── requirements.txt
└── README.md
```

## 21. Module Interfaces
- `FaceEngine.get_embedding(image_bytes) -> np.ndarray`
- `FaceEngine.compare(emb1, emb2) -> float`
- `ReverseImageSearcher.search(image_bytes) -> List[SearchCandidate]`
- `CandidateProcessor.evaluate(candidates, source_emb) -> CandidateEvaluation`
- `EvidenceBuilder.build(candidate_eval) -> EvidenceManifest`
- `HashService.canonical_hash(manifest) -> str`
- `EvidenceRegistryClient.register(hash_str) -> str (tx_hash)`
- `EvidenceRegistryClient.verify(hash_str) -> bool`

## 22. Data Contracts
See Section 11 & 12. Pydantic or Dataclasses should be used in `src/models.py`.

## 23. Pipeline State Machine
`IDLE` -> `INPUT_VALIDATED` -> `FACE_DETECTED` -> `FACE_EMBEDDED` -> `SEARCHING` -> `SEARCH_COMPLETE` -> `CANDIDATES_PROCESSING` -> `MATCH_FOUND` | `NO_MATCH` -> `EVIDENCE_CREATED` -> `HASH_CREATED` -> `BLOCKCHAIN_SUBMITTING` -> `BLOCKCHAIN_CONFIRMED` -> `VERIFYING` -> `VERIFIED` | `TAMPERED_OR_UNREGISTERED`.

## 24. Dependency Graph
```
Config -> Face Engine
Config -> Search Adapter
Search Adapter -> Candidate Processor
Face Engine -> Candidate Processor
Candidate Processor -> Evidence Builder
Evidence Builder -> Hash Service
Hash Service -> Blockchain Client
All -> Pipeline Orchestrator -> Streamlit UI
```
(Parallel tracks: Face Engine setup and Blockchain Contract deployment can happen simultaneously).

## 25. Build Phases
- **Phase 0**: Analysis and planning (COMPLETE).
- **Phase 1**: Repository foundation & Face Engine (T1, T2).
- **Phase 2**: Search Provider & Candidate Verification (T3, T4, T5, T6).
- **Phase 3**: Evidence, Hashing & Blockchain Client (T7, T8, T9, T10).
- **Phase 4**: Streamlit UI integration & E2E Pipeline (T11).
- **Phase 5**: Testing, Hardening, and Demo Script validation (T12, T13, T14).

## 26. Granular Agent Backlog
- `FND-001`: Repo init, `.env.example`, `requirements.txt`.
- `FND-002`: `src/config.py` and `src/models.py`.
- `FACE-001`: `src/face.py` implementation with InsightFace.
- `FACE-002`: Tests for face detection and embedding.
- `SEARCH-001`: `src/reverse_search.py` interface and mock provider for testing.
- `MATCH-001`: `src/candidate.py` image download and face evaluation logic.
- `EVD-001`: `src/evidence.py` and `src/hashing.py` (canonicalization).
- `BC-001`: `contracts/EvidenceRegistry.sol`.
- `BC-002`: `src/blockchain.py` web3 client wrapper.
- `PIP-001`: `app/pipeline.py` orchestrator.
- `UI-001`: `app/ui.py` Streamlit frontend.

## 27. Individual Agent Task Contracts
*(Sample Contract for Phase 1)*
**TASK ID**: FACE-001
**Objective**: Implement `FaceEngine` protocol using InsightFace.
**Files to create**: `src/face.py`, `tests/test_face.py`
**Input**: Image bytes.
**Expected Output**: Normalized ArcFace embedding (NumPy array).
**Acceptance Criteria**: Must detect a face, extract embedding, and compute cosine similarity accurately between two identical/different embeddings. Handle multiple faces by returning an error or selecting the largest.

## 28. Testing Strategy
- **Unit**: Tests for hashing determinism, cosine similarity logic, candidate filtering.
- **Integration**: Mock provider returns JSON -> candidate processing -> pipeline state.
- **Blockchain**: Local Ganache/Anvil or Polygon Amoy testnet tests for contract deployment and registry.
- **Tamper**: Automated test validating `hash(modified_evidence) != hash(original_evidence)`.

## 29. Failure Matrix
| Failure | Detection | User Message | Retry | Recovery |
|---|---|---|---|---|
| Invalid image | Decode fails | "Invalid image format." | No | Prompt new upload |
| No face | Face count == 0 | "No face detected in image." | No | Prompt new upload |
| Search limit | Provider HTTP 429 | "Search quota exceeded." | Yes | Backoff / Fail |
| No match | Max sim < Threshold | "NO VERIFIED MATCH FOUND" | No | End pipeline cleanly |
| RPC Down | Web3 timeout | "Blockchain network unavailable" | Yes | Fallback RPC / Fail |

## 30. Risk Register
1. **API Rate Limits / Pricing (High)**: Use mock tests during dev. Only use live search for final E2E testing and recording.
2. **GPU Availability (Medium)**: Use CPU-based ONNX execution for broader compatibility.
3. **Smart Contract Gas (Low)**: Testnet faucets provide sufficient Amoy MATIC.
4. **False Face Matches (Medium)**: Display similarity clearly, state "Experimental threshold", ensure UI doesn't claim absolute identity.

## 31. Fallback Strategy
- **Search Provider Unavailable**: Switch to `Local Test Mode` with pre-defined fixtures to keep UI demo functional.
- **RPC Unavailable**: Fallback to public backup Polygon Amoy RPCs.
- **Candidate Image Blocks**: Skip candidate, continue processing others.

## 32. Demo Plan
1. Start App (`LIVE SEARCH`).
2. Upload Face Scan. Observe face box and embedding generation.
3. Click "Genuine Search". Watch dynamic candidate retrieval.
4. Watch independent face similarity comparison.
5. Display Best Matching Candidate.
6. Display Evidence Manifest and SHA-256 fingerprint.
7. Click "Register to Blockchain". Confirm Polygon Amoy Tx Hash.
8. Click "Verify". Confirm `VERIFIED` state.
9. Click "Tamper Demo" (modify evidence). Confirm `TAMPER DETECTED` state.
10. Click "Restore". Confirm `VERIFIED` state.

## 33. Submission Plan
- Finalize `README.md`.
- Ensure `.env` is absent, `.env.example` is complete.
- Verify `requirements.txt` runs on a fresh clone.
- Record demo as per Demo Plan.
- Upload unedited video.

## 34. Definition of Done (Phase 0)
Phase 0 is complete. A concrete execution roadmap exists that eliminates architectural ambiguity, defines data contracts, specifies safety fallbacks, and scopes the project strictly to the required pipeline without unauthorized feature bloat.

## 35. Recommended Build Order
1. Repo Foundation, Models, and Config (Phase 1)
2. Face Engine (Phase 1)
3. Hashing and Evidence (Phase 3 Prep)
4. Candidate Retrieval & Comparison Logic (Phase 2)
5. Search Provider API (Phase 2)
6. Smart Contract & Web3 Client (Phase 3)
7. State Machine / Pipeline (Phase 4)
8. Streamlit UI (Phase 4)

## 36. Immediate Next Action
Proceed to Phase 1: Foundation and Face Engine implementation.
