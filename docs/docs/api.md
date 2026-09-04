# API and External Services

## 1. Reverse Image Search

Use a legitimate reverse-image-search API/provider.

The implementation must document:
- provider name
- API version where applicable
- authentication mechanism
- request format
- response format
- rate limits
- terms/usage restrictions
- image retention behavior if documented

Do not claim a provider supports functionality that its current API documentation does not provide.

## 2. Polygon RPC

Configuration:

```text
POLYGON_RPC_URL=...
```

Use the current official Polygon documentation to obtain the correct endpoint.

## 3. Smart Contract

Configuration:

```text
CONTRACT_ADDRESS=...
CONTRACT_ABI_PATH=...
```

## 4. Wallet

Configuration:

```text
PRIVATE_KEY=...
WALLET_ADDRESS=...
```

Never commit the private key.

## 5. API Error Categories

Handle:
- authentication failure
- quota/rate limit
- timeout
- malformed response
- provider unavailable
- no results

## 6. Retry Policy

Use bounded retries only for transient failures.

Example:
- 3 attempts
- exponential backoff
- no retry for authentication errors

## 7. Network Timeouts

Every HTTP request should have a timeout.

Never allow a UI request to hang indefinitely.

## 8. Provider Abstraction

Application code should call:

```python
searcher.search(image)
```

rather than directly depending on provider-specific response formats.

This allows provider replacement.
