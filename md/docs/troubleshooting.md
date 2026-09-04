# Troubleshooting

## Face model does not load

Check:
- Python version
- InsightFace installation
- ONNX Runtime
- model download/cache
- CPU/GPU configuration

## No face detected

Try:
- higher resolution
- better lighting
- frontal image
- clear image

## Search returns no results

Possible causes:
- provider index coverage
- image not previously indexed
- provider quota
- network issue

Do not hardcode a target just to make the demo pass. Use a known test image only if it is genuinely submitted through the search flow.

## Candidate page cannot be retrieved

Possible causes:
- robots/access restrictions
- login requirement
- dynamic rendering
- dead link

Try another dynamically returned candidate.

## Face similarity is low

Check:
- same model
- alignment
- image quality
- correct input face
- multiple-face selection
- threshold calibration

## Transaction fails

Check:
- testnet wallet balance
- RPC URL
- chain ID
- contract address
- ABI
- nonce
- gas
- private key configuration

## Verification fails after original registration

Check:
- canonicalization
- JSON key ordering
- timestamp changes
- floating-point serialization
- whitespace
- changed metadata
- image file bytes

The manifest used for verification must be reconstructed deterministically.

## Tamper demo always passes

You may be verifying only a stored hash rather than recalculating the current evidence.

Correct:

```text
current evidence → hash → compare to chain
```

Incorrect:

```text
stored hash → compare to same stored hash
```

## Private key accidentally exposed

Immediately:
1. stop using the wallet,
2. revoke/replace relevant credentials,
3. remove secrets from Git history if needed,
4. use a new testnet wallet.
