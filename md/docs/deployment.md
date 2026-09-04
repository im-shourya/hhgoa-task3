# Deployment and Running

## 1. Local Setup

```bash
git clone <YOUR_REPOSITORY>
cd hh-goa-task3

python -m venv .venv
```

Activate the environment according to your operating system.

Install:

```bash
pip install -r requirements.txt
```

## 2. Environment

Copy:

```text
env.example → .env
```

Fill only local secrets/configuration.

## 3. Contract

Deploy `EvidenceRegistry.sol` to Polygon Amoy.

Save:
- contract address
- ABI

## 4. Run UI

Recommended:

```bash
streamlit run app/ui.py
```

## 5. CLI Test

Optional:

```bash
python scripts/search_test.py data/input/face_scan.jpg
```

## 6. Blockchain Test

Optional:

```bash
python scripts/verify_test.py
```

## 7. Production Warning

This is a prototype. Do not use a valuable mainnet wallet or real private biometric datasets without a proper security/privacy review.
