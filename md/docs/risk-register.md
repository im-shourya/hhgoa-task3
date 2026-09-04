# Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Search provider returns no candidate | High | Medium | Validate provider early; support provider abstraction |
| Candidate page inaccessible | Medium | High | Process multiple candidates |
| Face false positive | High | Medium | Calibrated threshold; independent evidence |
| Face false negative | High | Medium | Better reference images; quality checks |
| RPC outage | Medium | Low/Medium | Retry; verify network before demo |
| Testnet funds unavailable | Medium | Medium | Fund wallet early |
| Private key leak | Critical | Low | `.env`, secret audit |
| API quota exceeded | High | Medium | Monitor quota; avoid repeated searches |
| Evidence changed during verification | Expected | Medium | Deterministic manifest |
| Demo fails due to internet | High | Medium | Test beforehand; have a clearly labeled local test mode |
