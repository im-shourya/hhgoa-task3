# Ethics, Privacy, and Responsible Use

## 1. Intended Use

This project is a technical demonstration of:
- face recognition
- public web discovery
- evidence integrity

It should not be presented as a general-purpose surveillance system.

## 2. Consent

Use images for testing where:
- the person has consented, or
- the content is appropriate for the intended demonstration and use is legally/contractually permitted.

## 3. Data Minimization

Only collect what is needed:
- image needed for recognition/search
- public candidate evidence
- minimal metadata
- cryptographic fingerprint

## 4. Biometric Protection

Do not:
- publish embeddings
- store unnecessary embeddings
- put embeddings on-chain
- create a permanent biometric identity database

## 5. Search Boundaries

Do not attempt:
- private account discovery
- authentication bypass
- CAPTCHA bypass
- credential theft
- restricted-data extraction

## 6. Accuracy

A high similarity score is not absolute identity proof.

The UI should use language such as:
- `Face similarity`
- `Candidate match`
- `Experimental threshold`

Avoid:
- `100% identity`
- `legally confirmed person`
- `guaranteed same person`

## 7. Blockchain Claims

Use:
`Fingerprint matches on-chain record`

Avoid:
`Blockchain proves the post is true`

## 8. Demo Data

Prefer a controlled test image and a publicly accessible test post designed for demonstration when possible.
