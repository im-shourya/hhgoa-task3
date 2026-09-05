# Architecture

## High-Level Architecture

```text
                         USER
                          │
                          ▼
                    Input Image
                          │
                          ▼
                  ┌───────────────┐
                  │   Stage 1     │
                  │ InsightFace   │
                  └───────┬───────┘
                          │
                   Face Embedding
                          │
                          ▼
                  ┌───────────────┐
                  │   Stage 2     │
                  │ Reverse Search│
                  └───────┬───────┘
                          │
                    Candidate URLs
                          │
                          ▼
                  Candidate Images
                          │
                          ▼
                  Candidate Faces
                          │
                          ▼
                  Face Similarity
                          │
                          ▼
                    Matching Post
                          │
                          ▼
                  ┌───────────────┐
                  │   Evidence    │
                  │    Bundle     │
                  └───────┬───────┘
                          │
                       SHA-256
                          │
                          ▼
                  ┌───────────────┐
                  │   Stage 3     │
                  │   Polygon     │
                  └───────┬───────┘
                          │
                     On-chain hash
                          │
                          ▼
                    Verification
```

## Separation of Concerns

Retrieval:
`reverse_search.py`

Recognition:
`face.py`

Evidence:
`evidence.py`

Integrity:
`hashing.py`

Blockchain:
`blockchain.py`

Presentation:
`ui.py`

## Design Principle

Every stage produces a structured output consumed by the next stage.

This avoids a monolithic script and makes failures observable.
