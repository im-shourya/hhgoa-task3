# Required Features

## 1. Face Input
- upload image
- image validation
- preview

## 2. Face Detection
- detect face
- show bounding box
- show detection count
- handle no-face case

## 3. Face Encoding
- generate embedding
- model status
- record model/configuration identifier

## 4. Genuine Web Search
- call reverse-image provider dynamically
- receive candidate results
- normalize results
- retain provider metadata

## 5. Candidate Evaluation
- retrieve candidate image where permitted
- detect candidate faces
- calculate similarities
- rank candidates
- identify best qualifying candidate

## 6. Match Presentation
Display:
- source
- URL
- candidate image
- face similarity
- match status

## 7. Evidence Creation
Create:
- manifest
- image hash
- source metadata
- search metadata
- observed timestamp

## 8. Blockchain Registration
- calculate SHA-256
- connect to Polygon Amoy
- call smart contract
- wait for confirmation
- show transaction hash

## 9. Blockchain Verification
- reconstruct manifest
- recalculate hash
- read blockchain
- compare
- show `VERIFIED` or `TAMPERED`

## 10. Tamper Demo
- allow test evidence modification
- show mismatch
- restore and verify again

## 11. Logging
Log:
- stage
- success/failure
- candidate counts
- transaction state
- errors without secrets

## 12. README
README must explain:
- what it does
- setup
- run commands
- blockchain
- provider configuration
- limitations
- demo flow
