# Stage 1 — Face Identification

## 1. Objective

Detect and encode a face from an input image.

The stage has four conceptual steps:

```text
Input image
  ↓
Decode
  ↓
Face detection
  ↓
Face selection
  ↓
Face embedding
```

## 2. Input

Example:

```text
data/input/face_scan.jpg
```

The image may contain one or more faces.

## 3. Face Detection

Use InsightFace to detect:
- bounding box
- confidence
- landmarks
- face object

Pseudo-flow:

```python
image = cv2.imread(path)
faces = app.get(image)
```

Do not assume a face exists.

Handle:
- no face
- multiple faces
- low-confidence detection
- unsupported/corrupt image

## 4. Face Selection

For a simple hackathon prototype:
- prefer exactly one detected face
- if multiple faces exist, require user selection or choose the largest only if clearly documented

Do not silently pick a random face.

## 5. Face Embedding

The selected face is converted into an embedding vector.

Conceptually:

```text
face crop
  ↓
alignment/preprocessing
  ↓
recognition model
  ↓
embedding vector
```

The embedding should be generated with the same model for all candidate images.

## 6. Normalization

Depending on the model/API, normalize embeddings before cosine similarity.

Example:

```python
embedding = embedding / np.linalg.norm(embedding)
```

Avoid double-normalizing if the library already returns normalized embeddings.

## 7. Similarity

Cosine similarity:

```text
cos(a,b) = (a·b) / (||a|| ||b||)
```

If embeddings are normalized, the dot product can be used.

Do not present a similarity score as a probability.

A score such as `0.92` means model-space similarity under the selected method; it does not mean "92% certain this is the same person."

## 8. Threshold

Do not blindly claim that one universal threshold proves identity.

Create a configurable value:

```text
FACE_MATCH_THRESHOLD=0.45
```

The exact value must be calibrated against the chosen model and test data.

For the demo, label it:

`Experimental threshold`

Document how it was chosen.

## 9. Stage 1 Output

Example:

```json
{
  "face_detected": true,
  "face_count": 1,
  "selected_face": 0,
  "embedding_generated": true
}
```

## 10. Privacy

Embeddings are biometric-derived information.

Recommended:
- use them transiently
- avoid storing unless needed
- never place embeddings on-chain
- never commit test images containing identifiable people without appropriate permission

## 11. Failure Handling

| Failure | UI result |
|---|---|
| Image cannot decode | Invalid image |
| No face | No face detected |
| Multiple faces | Select one / clarify |
| Low confidence | Detection quality warning |
| Model unavailable | Model initialization error |
| Embedding failure | Recognition error |

## 12. Definition of Done

Stage 1 is complete when:
- input image loads,
- face is detected,
- bounding box can be displayed,
- embedding is generated,
- failures are handled,
- model configuration is documented.
