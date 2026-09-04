# AGENTS.md — HH Goa 2026 Task 3

## Mission
Build a modular pipeline:
Face scan → face detection/embedding → genuine web/social discovery → candidate face verification → evidence manifest → SHA-256 fingerprint → blockchain registration → independent verification.

## Non-negotiable rules
1. Never hardcode the final social-media result.
2. Live mode must make a genuine provider request.
3. Fixture results are allowed only in LOCAL_TEST_MODE/tests.
4. Search ranking is not proof of a face match; independently compare faces.
5. Preserve provenance for every selected candidate.
6. Hash canonical evidence, not arbitrary Python representations.
7. Store fingerprints on-chain, never raw face embeddings.
8. Verification must recompute the fingerprint from current evidence.
9. UI must clearly label LIVE vs LOCAL_TEST_MODE.
10. Never commit API keys, private keys, seed phrases, or .env files.
11. Never bypass authentication, CAPTCHAs, privacy controls, or private-account restrictions.
12. Do not describe a similarity score as proof of legal identity.
13. Do not describe blockchain registration as proof that a post is true.
14. External providers must be behind interfaces/adapters.
15. All network calls require bounded timeouts.
16. Every pipeline stage needs explicit success/failure states.

## Agent workflow
Before coding, read:
- docs/requirements-traceability.md
- docs/architecture.md
- docs/data-model.md
- docs/testing.md
- relevant stage specification

While coding:
- preserve module boundaries
- use type hints
- add tests for non-trivial logic
- do not swallow exceptions
- do not log secrets
- document dependency additions
- update docs if behavior/schema changes

After coding:
- run tests
- run compile/lint checks if configured
- run LOCAL_TEST_MODE
- run live integration only when credentials are configured
- run blockchain testnet integration separately
- run tamper test
- inspect git diff for secrets

## Definition of complete
A feature is complete only when implementation, tests, error paths, documentation, and acceptance criteria are all satisfied.
