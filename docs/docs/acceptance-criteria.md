# Acceptance Criteria

## Mandatory

### AC1 — Face
Given a valid face image:
- system detects a face
- system generates an embedding

### AC2 — Genuine Search
Given the input image:
- system performs a real search
- candidate results come dynamically from provider response
- final URL is not hardcoded

### AC3 — Matching Post
Given a suitable public candidate:
- system retrieves candidate content
- system detects candidate face
- system computes similarity
- system identifies a qualifying candidate

### AC4 — Evidence
System creates:
- source URL
- candidate image hash
- metadata
- canonical manifest

### AC5 — Blockchain
System:
- hashes evidence
- registers fingerprint on blockchain
- receives successful transaction

### AC6 — Verification
System:
- recomputes fingerprint
- reads blockchain record
- reports matching evidence as verified

### AC7 — Tamper
After changing evidence:
- fingerprint changes
- comparison fails
- UI reports tampering/integrity failure

### AC8 — Repository
GitHub repository contains:
- full source
- README
- setup
- blockchain information
- limitations

### AC9 — Recording
Screen recording shows:
- face
- search
- matching post
- blockchain transaction
- verification

## Quality Criteria

- no hardcoded target URL
- no exposed secrets
- errors handled
- source URL retained
- transaction hash retained
- terminology is accurate
- claims are not overstated
