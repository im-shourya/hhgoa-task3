# Testing

## 1. Unit Tests

### Face
- valid image
- no face
- multiple faces
- embedding generated
- similarity function

### Search
- valid provider response
- empty results
- malformed result
- duplicate URL
- provider error

### Evidence
- deterministic canonical JSON
- stable manifest hash
- changed field changes hash

### Blockchain
- contract ABI loads
- fingerprint converts to bytes32
- transaction receipt status
- read-back record

## 2. Integrity Test

Given identical evidence:

```text
hash1 == hash2
```

After changing one field:

```text
hash1 != hash3
```

## 3. End-to-End Test

```text
input
 ↓
face
 ↓
search
 ↓
candidate
 ↓
match
 ↓
manifest
 ↓
hash
 ↓
chain
 ↓
verify
```

## 4. Tamper Test

1. Register original.
2. Verify original.
3. Change evidence.
4. Verify changed evidence.
5. Expect mismatch.
6. Restore.
7. Expect match.

## 5. Network Failure Tests

Simulate:
- provider timeout
- provider 429
- RPC unavailable
- transaction rejected
- insufficient testnet funds

The UI should show actionable errors.

## 6. Security Test

Before GitHub push:

```bash
git status
```

Search for:
- `PRIVATE_KEY=`
- API keys
- secrets
- seed phrases

Do not upload real private data.
