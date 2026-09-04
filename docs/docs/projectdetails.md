# Project Details

## 1. Project Name

HH Goa 2026 — Task 3: Face Identification & Blockchain Verification

## 2. Problem Statement

Given a user-provided face scan, discover publicly accessible web/social content that may contain the same face, independently compare the discovered face to the input, and create a tamper-evident blockchain record of the discovered evidence.

## 3. Core Pipeline

```text
Face scan
  ↓
Face detection
  ↓
Face embedding
  ↓
Reverse image search
  ↓
Candidate URLs/images
  ↓
Candidate face detection
  ↓
Candidate embeddings
  ↓
Similarity ranking
  ↓
Matching post
  ↓
Evidence manifest
  ↓
SHA-256
  ↓
Polygon Amoy smart contract
  ↓
Transaction
  ↓
Recompute hash
  ↓
On-chain comparison
  ↓
VERIFIED / TAMPERED
```

## 4. Inputs

Minimum:
- one image containing a detectable face

Potential future inputs:
- multiple face images
- video frame
- webcam frame
- cropped face

## 5. Outputs

The application should produce:
- detected-face visualization
- input embedding status
- number of search candidates
- candidate URLs
- candidate images where accessible
- face similarity scores
- selected matching result
- evidence manifest
- SHA-256 fingerprint
- blockchain transaction hash
- block number
- registration timestamp
- on-chain verification result
- tamper-check result

## 6. Scope

### In scope
- single-image face analysis
- dynamic reverse-image search
- candidate retrieval
- candidate face comparison
- public/testnet blockchain registration
- evidence integrity verification
- demo UI
- GitHub-ready documentation

### Out of scope
- guaranteed identity attribution
- bypassing platform access controls
- private-account access
- authentication bypass
- unauthorized scraping
- storing biometric embeddings on-chain
- legal certification of evidence
- guaranteed recognition under all image conditions

## 7. Success Definition

A successful run should dynamically discover at least one candidate that:
1. originates from the search provider response,
2. is publicly accessible or otherwise legitimately retrievable,
3. contains a detectable face,
4. reaches the configured experimental similarity threshold,
5. has a recorded source URL,
6. becomes part of an evidence manifest,
7. produces a fingerprint recorded on-chain,
8. can later be reverified.

## 8. Design Philosophy

Use the search engine for discovery, the face model for comparison, and the blockchain for integrity anchoring.

Do not make any one component claim what another component actually proves.
