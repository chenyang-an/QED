# Token Usage

**Primary Model:** `opus`  
**Started:** 2026-04-05 12:01:05  
**Last updated:** 2026-04-05 12:10:30  

## Summary

| Metric | Value |
|--------|-------|
| Total input tokens | 1,499,022 |
| Total output tokens | 100,845 |
| Total tokens | 1,599,867 |
| Total elapsed | 1602s |
| Agent calls | 16 |

## Per-Provider Summary

| Provider | Model | Input | Output | Total | Calls |
|----------|-------|------:|-------:|------:|------:|
| claude | opus | 17,507 | 27,193 | 44,700 | 8 |
| codex | gpt-5.4 | 1,323,939 | 57,765 | 1,381,704 | 4 |
| gemini | gemini-3.1-pro-preview | 157,576 | 15,887 | 173,463 | 4 |

## Per-Call Breakdown

| # | Agent | Provider | Input | Output | Time | Cumul In | Cumul Out |
|---|-------|----------|------:|-------:|-----:|---------:|----------:|
| 1 | Literature Survey | claude | 355 | 1,713 | 40.4s | 355 | 1,713 |
| 2 | Proof Search R1 [gemini] | gemini | 28,371 | 2,079 | 53.2s | 28,726 | 3,792 |
| 3 | Proof Search R1 [claude] | claude | 2,232 | 3,895 | 70.2s | 30,958 | 7,687 |
| 4 | Proof Search R1 [codex] | codex | 262,529 | 7,720 | 131.0s | 293,487 | 15,407 |
| 5 | Verification R1 [gemini] [gemini] | gemini | 35,670 | 2,877 | 45.4s | 329,157 | 18,284 |
| 6 | Verification R1 [codex] [gemini] | gemini | 49,257 | 5,031 | 65.9s | 378,414 | 23,315 |
| 7 | Verification R1 [claude] [gemini] | gemini | 44,278 | 5,900 | 70.3s | 422,692 | 29,215 |
| 8 | Verification R1 [claude] [claude] | claude | 2,896 | 5,067 | 75.6s | 425,588 | 34,282 |
| 9 | Verification R1 [codex] [claude] | claude | 4,012 | 4,796 | 79.2s | 429,600 | 39,078 |
| 10 | Verification R1 [gemini] [claude] | claude | 5,442 | 5,868 | 90.5s | 435,042 | 44,946 |
| 11 | Verification R1 [claude] [codex] | codex | 385,554 | 16,946 | 230.9s | 820,596 | 61,892 |
| 12 | Verification R1 [codex] [codex] | codex | 308,855 | 15,748 | 255.7s | 1,129,451 | 77,640 |
| 13 | Verification R1 [gemini] [codex] | codex | 367,001 | 17,351 | 271.4s | 1,496,452 | 94,991 |
| 14 | Proof Selection R1 | claude | 2 | 2,015 | 37.4s | 1,496,454 | 97,006 |
| 15 | Verdict R1 | claude | 2 | 222 | 8.0s | 1,496,456 | 97,228 |
| 16 | Proof Effort Summary | claude | 2,566 | 3,617 | 76.8s | 1,499,022 | 100,845 |
