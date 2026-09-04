# HH Goa 2026 — Task 3: Face Identification & Blockchain Verification

## 1. Project Overview

This project implements an end-to-end research/prototype pipeline:

**Face scan input → face detection/encoding → genuine web/social-media discovery → candidate face verification → evidence packaging → cryptographic fingerprint → blockchain registration → independent re-verification → tamper detection**

The project is intentionally designed as a pipeline rather than a website-heavy product. A Streamlit interface is recommended for demonstrating the pipeline, but the core logic remains modular and runnable from Python.

### Core principle

The web-search stage retrieves candidates dynamically. It must not contain a pre-selected target URL.

The face-recognition stage independently verifies whether a face in a discovered candidate resembles the input face.

The blockchain stage does not claim to prove a person's real-world identity. It proves that the evidence currently being verified has the same cryptographic fingerprint as the evidence previously registered on-chain.

## 2. Requirement Mapping

| Task requirement | Implementation |
|---|---|
| Detect a face | InsightFace |
| Encode a face | ArcFace embedding from InsightFace |
| Search web/social media | Reverse-image-search provider/API |
| Genuine search | Candidate URLs originate dynamically from search response |
| Find matching post | Candidate images/pages are evaluated |
| Verify candidate face | Face embedding similarity |
| Upload post or fingerprint | SHA-256 fingerprint recorded on Polygon Amoy |
| Tamper-evident record | On-chain immutable registration |
| Re-verify | Recompute local fingerprint and compare to on-chain record |
| Demo | Streamlit + terminal logs + block explorer |

## 3. Recommended Stack

- Python 3.11+
- InsightFace
- ONNX Runtime / ONNX Runtime GPU where appropriate
- OpenCV
- Pillow
- NumPy
- requests
- BeautifulSoup4
- imagehash
- web3.py
- Solidity
- Polygon Amoy testnet
- Streamlit
- python-dotenv
- pytest

## 4. Documentation

- `techstack.md` — complete technology decisions
- `projectdetails.md` — project definition, scope, assumptions
- `filestructure.md` — repository structure
- `stage1.md` — face detection and encoding
- `stage2.md` — web/social discovery and candidate verification
- `stage3.md` — blockchain registration and re-verification
- `features.md` — required features
- `additionalfeatures.md` — optional enhancements
- `task.md` — original requirement translated into engineering tasks
- `buildphase.md` — implementation phases
- `plan.md` — schedule and execution plan
- `architecture.md` — end-to-end architecture
- `api.md` — API/provider contracts
- `data-model.md` — evidence and data structures
- `security.md` — secrets, privacy, and threat model
- `testing.md` — test strategy
- `demo.md` — screen-recording script
- `deployment.md` — local/demo deployment
- `limitations.md` — known limitations
- `acceptance-criteria.md` — definition of done
- `troubleshooting.md` — common failures
- `decisions.md` — architecture decision record
- `ethics.md` — responsible-use considerations
- `env.example` — environment variable template

## 5. Critical Demo

The strongest demonstration is:

1. Upload face scan.
2. Detect face and generate embedding.
3. Run a real reverse-image search.
4. Display dynamically discovered candidates.
5. Download/access candidate images where legally/publicly accessible.
6. Detect faces in candidates.
7. Compare candidate embeddings with input.
8. Display the strongest qualifying candidate and source URL.
9. Create an evidence manifest.
10. Calculate SHA-256.
11. Register fingerprint on Polygon Amoy.
12. Display transaction hash.
13. Open the transaction in a public block explorer.
14. Recompute the fingerprint.
15. Compare local and on-chain values.
16. Show `VERIFIED`.
17. Modify the evidence.
18. Recompute and show `TAMPER DETECTED`.
19. Restore the original evidence and show `VERIFIED` again.

## 6. Important Interpretation

The system has two distinct verification claims:

**Face verification:** the candidate contains a face whose embedding is sufficiently similar to the input under the selected model and experimental threshold.

**Blockchain verification:** the current evidence fingerprint matches the fingerprint registered on-chain.

The blockchain does not independently establish the person's legal identity, ownership of an account, truthfulness of a post, or authenticity of the source platform.

## 7. Security Rules

Never commit:
- private keys
- API keys
- access tokens
- passwords
- `.env`
- wallet seed phrases

Commit only `.env.example` / `env.example`.

Do not store face embeddings on-chain. Use them for local comparison only.

## 8. Status

This repository is a hackathon prototype. Provider capabilities, social-platform accessibility, model thresholds, and testnet infrastructure can change. All provider-specific implementation must be validated against the provider's current documentation before final submission.
