# Task 3 — Engineering Task Breakdown

## Original Goal

Build:

`Face scan input → Web/social media search → matching post → blockchain upload/verification`

## Work Breakdown

### T1 — Repository
- initialize Git
- create README
- create Python environment
- add `.gitignore`
- create docs structure

### T2 — Face Model
- install InsightFace
- initialize model
- detect face
- generate embedding
- handle failures

### T3 — Search Provider
- choose provider
- obtain API credentials
- implement interface
- submit image
- parse results
- normalize candidates

### T4 — Candidate Retrieval
- validate URL
- retrieve image/page
- store temporary evidence
- handle inaccessible results

### T5 — Candidate Face Verification
- detect faces
- embed each face
- compare to input
- rank
- apply documented threshold

### T6 — Matching Post
- select qualifying candidate
- display source URL
- preserve search provenance

### T7 — Evidence
- construct manifest
- canonicalize
- calculate image hash
- calculate manifest hash

### T8 — Blockchain
- write contract
- deploy to testnet
- integrate web3.py
- register fingerprint
- wait for receipt

### T9 — Verification
- recalculate fingerprint
- query chain
- compare
- show result

### T10 — Tamper Test
- modify evidence
- verify mismatch
- restore
- verify again

### T11 — UI
- stage indicators
- candidate results
- blockchain state
- verification state

### T12 — Testing
- unit tests
- search integration test
- blockchain test
- full pipeline test

### T13 — Documentation
- setup
- architecture
- limitations
- demo instructions
- provider details
- blockchain details

### T14 — Submission
- final GitHub push
- final screen recording
- verify repository
- submit form once
