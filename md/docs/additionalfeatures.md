# Additional Features

These are optional and should be implemented only after the mandatory pipeline works.

## Priority 1 — High Value

### 1. Candidate Evidence Table
Show every candidate:

| Rank | URL | Source | Face score | Status |
|---|---|---|---:|---|
| 1 | ... | ... | 0.92 | MATCH |
| 2 | ... | ... | 0.71 | REVIEW |

### 2. Search Provenance
Save:
- search timestamp
- provider
- result count
- normalized result metadata

### 3. Tamper Demo
One-click:
`Modify test evidence → Verify → TAMPERED`

### 4. Block Explorer Link
Display transaction hash and public explorer navigation.

### 5. Evidence Manifest Download
Allow downloading the JSON manifest.

## Priority 2

### 6. Multiple Reverse Search Providers
Use a provider abstraction and aggregate candidates.

### 7. Perceptual Hash
Use pHash for supporting visual similarity.

### 8. Screenshot Evidence
Capture the discovered public page when legally/technically appropriate.

### 9. Retry/Timeout System
Add bounded retries for network APIs.

### 10. Candidate Cache
Cache search results for repeat debugging without pretending cached results are live search results.

## Priority 3

### 11. Multi-Face Input
Allow selecting which input face to search.

### 12. Multi-Image Verification
Use several reference images and aggregate evidence.

### 13. Confidence Calibration
Build a local benchmark of positive/negative pairs and select a threshold from observed distributions.

### 14. Evidence Merkle Tree
For multiple files, create a Merkle root and store only the root on-chain.

### 15. IPFS
Optionally store an encrypted/public evidence package off-chain and put its content identifier plus hash on-chain. Only do this if the privacy model is understood.

### 16. Contract Events
Use events to make evidence registrations easier to inspect.

### 17. Exportable Verification Report
Generate a JSON/PDF report containing:
- source
- match score
- evidence hash
- tx hash
- verification result
- timestamps

### 18. CLI
Support:

```bash
python -m app.pipeline --input image.jpg
```

## Features to Avoid Unless Explicitly Needed

- private-account access
- credential scraping
- anti-bot bypass
- identity database lookup
- storing face embeddings on-chain
- collecting unnecessary personal data
- automatic claims of legal identity
