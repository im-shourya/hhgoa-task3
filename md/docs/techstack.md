# Tech Stack

## 1. Stack Summary

### Recommended primary stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.11+ | Fast integration and ML/API ecosystem |
| UI | Streamlit | Fast hackathon demo |
| Face detection/recognition | InsightFace | Face detection + ArcFace embeddings |
| Inference | ONNX Runtime | Efficient model execution |
| Image processing | OpenCV + Pillow | Decoding, resizing, image operations |
| Numerical operations | NumPy | Embedding/vector operations |
| Reverse image search | Provider API such as TinEye | Dynamic image-to-web discovery |
| Web parsing | requests + BeautifulSoup4 | Candidate page/image extraction |
| Image similarity | imagehash | Optional perceptual similarity |
| Hashing | Python hashlib / SHA-256 | Evidence fingerprint |
| Blockchain | Polygon Amoy | Public EVM testnet |
| Smart contract | Solidity | Minimal evidence registry |
| Blockchain client | web3.py | Python/EVM integration |
| Configuration | python-dotenv | Environment variables |
| Testing | pytest | Unit/integration tests |
| Formatting | Ruff/Black, optional | Code quality |
| Version control | Git + GitHub | Submission |

## 2. Why InsightFace

InsightFace can provide:
- face detection
- facial landmarks
- face alignment
- face embeddings
- recognition-oriented models

The project should use the same model/configuration for the input face and candidate faces.

## 3. Why reverse-image search

A face embedding is not normally a web-search query.

The correct architecture is:

`input image → reverse-image search → candidate web content → face verification`

This separates retrieval from identity comparison.

## 4. Why Polygon Amoy

A public testnet makes the record independently inspectable without the cost/risk of production mainnet use.

Use the current official Polygon documentation for:
- RPC configuration
- chain ID
- testnet status
- faucet instructions
- explorer

Do not hardcode undocumented endpoints into the repository.

## 5. Why SHA-256

SHA-256 provides an exact cryptographic fingerprint for the canonical evidence representation.

It is suitable for:
- image file fingerprinting
- evidence manifest fingerprinting
- deterministic integrity checks

It does not provide semantic similarity.

## 6. Why perceptual hashing is optional

pHash/dHash/aHash are useful for visual similarity after:
- recompression
- resizing
- small transformations

They are not substitutes for SHA-256 when proving exact byte-level integrity.

## 7. Dependency separation

Keep these modules separate:

- `face.py`
- `reverse_search.py`
- `candidate.py`
- `evidence.py`
- `hashing.py`
- `blockchain.py`
- `ui.py`

This makes provider replacement easier.

## 8. Production-vs-hackathon tradeoff

The project prioritizes:
1. demonstrability
2. modularity
3. reproducibility
4. transparent evidence
5. privacy-aware design

It does not attempt to become a production identity platform.
