# Privacy Design

## Data Flow

Input image:
`local → face model → search provider if reverse-search upload is required`

Candidate data:
`provider/page → temporary processing → evidence manifest`

Embedding:
`local processing → not stored on-chain`

Fingerprint:
`local hash → public blockchain`

## Principle

The blockchain should contain the minimum necessary information:
- fingerprint
- timestamp
- submitting wallet

Not:
- face embedding
- raw image
- private post text
- unnecessary personal information
