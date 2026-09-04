# Stage 2 — Social Media / Web Search

## 1. Objective

Use the input image to perform a genuine reverse-image/web search, dynamically discover candidate pages/images, and independently verify which candidate contains a sufficiently similar face.

## 2. Critical Interpretation

Do not do:

```python
return "https://known-target.com/post"
```

Do:

```text
input image
  ↓
search provider API
  ↓
dynamic results
  ↓
candidate URLs
  ↓
candidate images
  ↓
face verification
```

## 3. Why the Face Embedding Is Not the Web Query

A face embedding is a numerical vector. General search engines do not normally accept that vector and return social posts.

Therefore:
- use the original image as the reverse-search signal,
- use the face embedding after retrieval to independently verify candidates.

This is one of the most important architectural decisions.

## 4. Provider Abstraction

Define an interface:

```python
class ReverseImageSearcher:
    def search(self, image_path):
        raise NotImplementedError
```

Then implement providers independently.

Example:
- `TinEyeSearcher`
- future provider

Provider credentials belong in environment variables.

## 5. Search Request

The implementation should:
1. read the input image,
2. submit it through the provider API,
3. receive a result set,
4. normalize each result.

A normalized candidate should contain fields such as:

```json
{
  "url": "...",
  "image_url": "...",
  "title": "...",
  "source_domain": "...",
  "provider": "..."
}
```

## 6. Genuine Search Requirement

The system must not:
- hardcode the final post,
- always return the same candidate,
- hide a predefined target URL,
- fabricate search results.

The final candidate must be traceable to a live/dynamic provider response during the run.

## 7. Candidate Filtering

Process:
- remove duplicate URLs
- normalize URLs
- reject unsupported protocols
- discard inaccessible results
- identify likely social/web sources
- prefer pages with retrievable images

Social domains may be classified, but the list must not contain the target result as a shortcut.

## 8. Candidate Image Retrieval

Where permitted and technically possible:
1. request candidate page,
2. inspect HTML,
3. extract publicly available image URLs,
4. download candidate image,
5. retain source URL.

Respect:
- robots.txt and applicable terms
- rate limits
- authentication boundaries
- platform restrictions

Do not bypass private accounts or access controls.

## 9. Candidate Face Verification

For every usable candidate image:

```text
candidate image
  ↓
InsightFace
  ↓
0..N detected faces
  ↓
candidate embeddings
  ↓
compare each to input embedding
```

Example:

```text
Candidate A:
face 1 = 0.51
face 2 = 0.67

Candidate B:
face 1 = 0.91  ← best

Candidate C:
face 1 = 0.43
```

Select the best face score for each candidate.

## 10. Ranking

Rank by face similarity:

```python
candidates.sort(
    key=lambda x: x["face_similarity"],
    reverse=True
)
```

Do not blindly accept the first web-search result.

## 11. Match Decision

A candidate can be labeled `MATCH` only if:
- image was successfully retrieved,
- at least one face was detected,
- similarity passes the configured experimental threshold,
- source URL is retained.

If nothing qualifies:

`NO VERIFIED MATCH FOUND`

This is preferable to fabricating a result.

## 12. Evidence to Capture

For the selected candidate:
- source URL
- source domain/platform
- image bytes
- image hash
- post text where publicly available
- page title
- observed timestamp
- search provider
- search result metadata
- face similarity
- candidate face index
- relevant screenshot if captured

## 13. Search Result UI

Recommended screen:

```text
SEARCHING
✓ Search request sent
✓ Results received: 17
✓ Candidates processed: 11

BEST CANDIDATE
Source: ...
URL: ...
Face similarity: ...
Status: MATCH
```

## 14. Raw Search Evidence

Save a provider response snapshot where terms and privacy rules permit.

Example:

```text
evidence/search_response.json
```

This helps prove the search was genuine.

## 15. Optional pHash

Use perceptual hashing as a supporting signal:

```text
imagehash.phash(candidate)
```

Do not use pHash as a substitute for face verification or SHA-256 integrity.

## 16. Stage 2 Output

```json
{
  "match_found": true,
  "url": "...",
  "image_path": "...",
  "face_similarity": 0.923,
  "candidate_face_index": 1,
  "provider": "reverse-image-provider"
}
```

## 17. Definition of Done

Stage 2 is complete when:
- a real search request is executed,
- candidates are dynamically returned,
- no final URL is hardcoded,
- candidate images are evaluated,
- faces are independently compared,
- at least one real matching post can be demonstrated,
- evidence metadata is captured.
