# Google Lens Failure Matrix

The Google Lens Browser Provider is an automated scraping tool interacting with a live, dynamic web environment. The following matrix details expected failure conditions and the system's corresponding behaviors.

| Failure | Expected behavior |
| :--- | :--- |
| **Playwright missing** | Raises a clear dependency error during provider initialization. |
| **Chromium missing** | Raises a provider error with Playwright browser installation guidance (`playwright install chromium`). |
| **Navigation timeout** | Raises a `SearchError` due to search timeout. Does not return mock candidates. |
| **Upload failure** | Raises a `SearchError` indicating the Google Lens upload flow failed. |
| **CAPTCHA / Challenge** | Explicitly raises a `SearchError` detailing an automation restriction (Blocked status). |
| **DOM structure changed** | Gracefully skips unparseable results; raises `SearchError` if the core results container cannot be found. |
| **No results returned** | Returns an empty `SearchResult`. Does not fabricate candidates or fallback to mock data. |
| **Candidate missing image URL** | Candidate is skipped or returned as discovery-only (if Phase 3 supports it) without fabricating an image URL from input data. |
| **Candidate download failure** | Handled natively by Phase 3 (marked unavailable and skipped during face evaluation). |
| **InsightFace failure** | Handled natively by Phase 3 (verification error / failed match). |
| **Mock provider fallback** | Never silently used. If Google Lens is configured, it either succeeds or explicitly fails. |
