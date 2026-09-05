# Data Model

## 1. Candidate

```json
{
  "url": "string",
  "image_url": "string|null",
  "title": "string|null",
  "source_domain": "string",
  "provider": "string",
  "retrieved_at": "ISO-8601 timestamp"
}
```

## 2. Face Match

```json
{
  "candidate_url": "string",
  "candidate_face_index": 0,
  "similarity": 0.923,
  "threshold": 0.45,
  "match": true
}
```

## 3. Evidence Manifest

```json
{
  "schema_version": "1.0",
  "source_url": "string",
  "source_platform": "string|null",
  "observed_at": "ISO-8601 timestamp",
  "post_text": "string|null",
  "page_title": "string|null",
  "image_sha256": "64-char hex",
  "face_similarity": 0.923,
  "search_provider": "string"
}
```

## 4. Blockchain Record

```json
{
  "network": "Polygon Amoy",
  "contract_address": "0x...",
  "fingerprint": "64-char hex",
  "transaction_hash": "0x...",
  "block_number": 123,
  "registered_at": "ISO-8601 timestamp"
}
```

## 5. Verification Result

```json
{
  "local_fingerprint": "...",
  "on_chain_exists": true,
  "matches": true,
  "status": "VERIFIED"
}
```

## 6. Canonicalization Rule

- UTF-8
- sorted object keys
- fixed separators
- explicit schema version
- deterministic representation

Do not hash pretty-printed JSON if deterministic verification is required.
