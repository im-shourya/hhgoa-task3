# Screen Recording Plan

## Goal

Show one complete, understandable run without editing.

## Scene 1 — Start

Show repository/app.

Say:

> This pipeline takes a face image, dynamically searches the web for candidate content, independently verifies the candidate face, and records the resulting evidence fingerprint on Polygon Amoy.

## Scene 2 — Face Scan

Upload the image.

Show:
- face box
- face detected
- embedding generated

## Scene 3 — Genuine Search

Click search.

Show:
- search started
- provider
- result count
- dynamically returned URLs

Do not hide the candidate list.

## Scene 4 — Face Verification

Show:
- candidate images
- face count
- similarity scores
- best match

Explain:

> The search provider retrieves candidates; InsightFace independently evaluates the faces.

## Scene 5 — Evidence

Show:
- source URL
- image
- post metadata
- manifest
- SHA-256

## Scene 6 — Blockchain

Click register.

Show:
- Polygon Amoy
- transaction submission
- confirmation
- transaction hash

Open public block explorer if available.

## Scene 7 — Re-verification

Click verify.

Show:

```text
Local hash
On-chain hash
MATCH
VERIFIED
```

## Scene 8 — Tamper Test

Change the evidence.

Run verify.

Show:

```text
Local hash != on-chain hash
TAMPER DETECTED
```

Restore the original.

Show:

```text
VERIFIED
```

## Recording Quality

No editing is required.

Ensure:
- API keys are hidden
- private key is never visible
- personal/private content is not exposed
- text is readable
- transaction hash is visible
- entire pipeline is continuous
