# Security

## 1. Secrets

Never commit:
- private keys
- API keys
- bearer tokens
- wallet seeds
- passwords

Use environment variables.

## 2. `.env`

Example:

```text
REVERSE_SEARCH_API_KEY=
POLYGON_RPC_URL=
PRIVATE_KEY=
WALLET_ADDRESS=
CONTRACT_ADDRESS=
FACE_MATCH_THRESHOLD=
```

## 3. Private Key Handling

The private key should:
- exist only in local environment
- never be logged
- never be displayed
- never be included in screenshots
- never be sent to the UI

## 4. Biometric Data

Face embeddings can be sensitive biometric-derived data.

Recommended:
- process locally
- avoid persistence
- never put embeddings on-chain
- delete temporary files when practical
- use test/consented images for demonstrations

## 5. Web Access

Do not:
- bypass login
- defeat CAPTCHA
- access private accounts
- evade access controls
- scrape prohibited content

Use public/legitimate API access.

## 6. Evidence Integrity

The blockchain record should contain only the fingerprint and minimal registry metadata.

The raw evidence can remain off-chain.

## 7. Threat Model

Potential threats:
- evidence modified after registration
- malicious local files
- wrong candidate selected
- provider result manipulation
- stale search results
- API compromise
- leaked private key

Mitigations:
- SHA-256
- on-chain registration
- independent face comparison
- provenance logging
- secrets management
- explicit limitations

## 8. What Blockchain Does Not Solve

Blockchain cannot prove that the source content was truthful before registration.

It can show that a particular fingerprint was registered at a particular time.
