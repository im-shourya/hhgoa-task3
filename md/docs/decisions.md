# Architecture Decisions

## ADR-001 — Use Reverse Image Search for Retrieval

### Decision
Use a reverse-image-search provider rather than attempting to search the web directly with a face embedding.

### Reason
Embeddings are recognition features, not conventional web-search queries.

### Consequence
Search retrieves candidates; InsightFace verifies candidates.

## ADR-002 — Use Polygon Amoy

### Decision
Use a public EVM testnet.

### Reason
Easy smart-contract integration and independently inspectable transactions.

## ADR-003 — Store Hash, Not Raw Image

### Decision
Store SHA-256 fingerprint on-chain.

### Reason
Lower data footprint and better privacy.

## ADR-004 — Keep Embeddings Off-Chain

### Decision
Do not store face embeddings on blockchain.

### Reason
Biometric-derived information should not be permanently published.

## ADR-005 — Canonical Evidence Manifest

### Decision
Hash deterministic JSON rather than arbitrary serialization.

### Reason
Verification must produce the same fingerprint from the same logical evidence.

## ADR-006 — Independent Face Verification

### Decision
Do not trust reverse-search ranking as proof of face identity.

### Reason
Search engines retrieve visually related content; the project needs an independent face-comparison step.

## ADR-007 — Tamper Demonstration

### Decision
Include a deliberate evidence modification test.

### Reason
It directly demonstrates the purpose of the blockchain fingerprint.
