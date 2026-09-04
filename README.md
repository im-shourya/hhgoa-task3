# HH Goa 2026 Task 3 — Face Identification & Blockchain Verification

This repository implements the end-to-end pipeline for Face Scan -> Genuine Web/Reverse-Image Search -> Candidate Matching -> Blockchain Verification.

## Phase 1 Status
**Phase 1 (Repository Foundation & Face Identification Engine) is COMPLETE.**
- Stage 2 (Reverse Image Search) is **NOT implemented yet**.
- Stage 3 (Blockchain Verification) is **NOT implemented yet**.

## Installation

### Python Requirement
- **Python 3.11+** is required.

### Dependency Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration includes:
- `FACE_MODEL`: `buffalo_l`
- `FACE_MATCH_THRESHOLD`: `0.45`
- `MAX_IMAGE_SIZE`: `10485760` (10 MB)
- `REQUEST_TIMEOUT`: `30`

## Face Engine Overview
The Face Engine (`src/face.py`) abstracts the underlying InsightFace model (`buffalo_l`). It accepts raw image bytes, decodes them safely with OpenCV, and generates a normalized ArcFace embedding vector. It validates empty inputs, limits max image size, and strictly mandates a single face policy.

### CPU Execution
The engine is configured to use the `CPUExecutionProvider` by default for maximum compatibility across developer machines without requiring CUDA or GPUs.

### Testing Commands
Run the unit tests:
```bash
pytest -q
```
Verify code quality:
```bash
python -m compileall src
ruff check .
```

## Known Limitations
- **Model Downloads**: The InsightFace model weights (`buffalo_l.zip`) are downloaded dynamically to `~/.insightface/models/` upon the first initialization if not found locally.
- **Thresholds**: The `FACE_MATCH_THRESHOLD=0.45` is an experimental threshold used for candidate matching, not a legally binding identity verification claim.

## Licensing Note
**Important:** InsightFace package source code is under MIT license, but the pretrained models (such as `buffalo_l` and ArcFace weights) have non-commercial or research-use restrictions depending on their original datasets. Do not assume the model weights are free for unrestricted commercial use.
