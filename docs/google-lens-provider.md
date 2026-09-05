# Google Lens Browser Provider

## 1. Purpose
The Google Lens Browser Provider serves as an alternative web discovery mechanism for Phase 2 of the Face Identification & Blockchain Verification pipeline. It uses browser automation via Playwright to perform reverse image searches on Google Lens.

## 2. Why
The `GoogleVisionSearchProvider` (which uses the official Google Cloud Vision API) currently requires a billing-enabled Google Cloud account, which is unavailable for live evaluation. The Google Lens browser provider bypasses this limitation by automating the free, public Google Lens interface to fulfill the live web discovery and social media retrieval requirements of the hackathon.

## 3. Provider Role
Google Lens is strictly a **Stage 2 discovery mechanism**. It does *not* establish biometric identity, nor does it guarantee a match. It simply discovers candidate image URLs that are visually similar or related to the input image. Identity verification remains entirely the responsibility of **InsightFace** in Phase 3.

## 4. Architecture
```text
Input Image
    ↓
Google Lens (Playwright Browser)
    ↓
Discovered Results (Page & Image URLs)
    ↓
Candidate Retrieval
    ↓
InsightFace (Biometric Verification)
    ↓
Match Decision
```

## 5. Limitations
- **Not an Official API:** This provider relies on browser automation interacting with a dynamic DOM. Google may alter the UI/DOM at any time.
- **Automation Blocks:** Google may block automation or present CAPTCHA challenges, which will cause the provider to fail securely rather than returning mock results.
- **Dynamic Content:** Result structures may shift; candidate URLs are only retrieved if they can be reliably extracted. Image URLs are never fabricated.
- **Domain Verification:** A discovered URL is not inherently a verified identity. Phase 3 face verification must independently validate the visual similarity before declaring a match.
