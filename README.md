# HH Goa 2026 Task 3 — Face Identification & Blockchain Verification

This repository implements the end-to-end pipeline for Face Scan -> Genuine Web/Reverse-Image Search -> Candidate Matching -> Blockchain Verification.

## Phase Status
- **Phase 1: Face engine implemented.** (Complete)
- **Phase 2: Search POC implemented.** (Complete)
- **Phase 3: Blockchain verification not yet implemented.**

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

#### Provider Configuration
- `PIPELINE_MODE`: Controls execution type (`local` or `live`).
- `SEARCH_PROVIDER`: Set to `google_vision` for live mode.
- `GOOGLE_API_KEY`: Required when using `GoogleVisionProvider` in live mode.

## Running the Search POC
The Search POC integrates external providers and matches dynamically fetched candidate images against the origin face embedding.

### LIVE mode
Set `PIPELINE_MODE=live` and configure `SEARCH_PROVIDER=google_vision` along with your `GOOGLE_API_KEY`. The system will upload your image via base64 encoded payload to Google Cloud Vision's `WEB_DETECTION` engine, parse the candidate pages and images, and evaluate the similarity securely on your local CPU.

### LOCAL mode
Set `PIPELINE_MODE=local`. The system skips external network search calls and relies on a `MockSearchProvider` returning local test candidate fixtures. Note: LOCAL MODE MUST NEVER BE PRESENTED AS LIVE SEARCH.

## Face Engine Overview
The Face Engine (`src/face.py`) abstracts the underlying InsightFace model (`buffalo_l`). It uses the `CPUExecutionProvider` by default.

### Testing Commands
Run the unit tests (works completely offline):
```bash
pytest -q
```
Verify code quality:
```bash
python -m compileall src
ruff check .
```

## Known Limitations & Privacy Implications
- **Model Downloads**: InsightFace model weights (`buffalo_l.zip`) download dynamically on the first initialization.
- **Image Transmission**: In LIVE mode, your query image bytes are base64 encoded and transmitted to the external configured provider (e.g., Google Cloud).
- **Candidate Storage**: Extracted face embeddings and downloaded candidate images are kept only in memory and never written to disk or logs.
- **Provider Limitations**: Google Vision web detection finds indexed public domains. Direct private social network scraping is not actively engaged without authenticated tokens for those specific properties.

## Licensing Note
InsightFace package source code is MIT licensed, but pretrained models (`buffalo_l`) have non-commercial or research-use restrictions based on their original datasets.
