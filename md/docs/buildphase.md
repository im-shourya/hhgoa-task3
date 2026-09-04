# Build Phase

## Phase 0 — Preparation

### Goal
Create a reproducible project.

Tasks:
- Python environment
- GitHub repo
- folder structure
- environment template
- README

Exit criteria:
- project starts
- dependencies install
- no secrets committed

## Phase 1 — Face Proof of Concept

Build:
- image upload
- InsightFace initialization
- detection
- embedding
- visualization

Exit:
`input image → embedding` works.

## Phase 2 — Search Proof of Concept

Build only a CLI:

```text
input.jpg
↓
reverse search
↓
print 10 candidates
```

Do not build blockchain yet.

Exit:
dynamic results are returned.

## Phase 3 — Candidate Verification

Build:
- image retrieval
- candidate face detection
- similarity
- ranking

Exit:
a real matching candidate can be demonstrated.

## Phase 4 — Evidence

Build:
- manifest
- canonical JSON
- SHA-256
- evidence folder

Exit:
same evidence produces the same fingerprint.

## Phase 5 — Smart Contract

Build/deploy:
- registry
- register
- verify
- event

Exit:
test transaction appears on Polygon Amoy.

## Phase 6 — Blockchain Integration

Connect Python:
- load RPC
- load ABI
- sign
- send
- wait for receipt
- query

Exit:
pipeline produces tx hash.

## Phase 7 — Re-verification

Build:
- recompute
- query
- compare
- tamper test

Exit:
original = VERIFIED
modified = TAMPERED

## Phase 8 — UI

Connect all stages.

Exit:
one button can execute the end-to-end flow.

## Phase 9 — Hardening

Add:
- error handling
- timeouts
- logs
- API failures
- blockchain failures
- no-match state

## Phase 10 — Documentation and Recording

Verify:
- clean README
- clean GitHub
- no secrets
- reproducible commands
- screen recording covers all stages

## Phase 11 — Final Freeze

Do not add risky features immediately before submission.

Run:
- clean installation
- full pipeline
- blockchain verification
- tamper test
- recording review
- repository review
