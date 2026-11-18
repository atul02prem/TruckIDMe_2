# Embedding verification — do the frozen embeddings match their source?

Reads the 12 files written by `src/features/build_embeddings.py` (3 tokens x 4 window lengths) and checks them against the window tensors, against each other, and against exp03's earlier `cls_token` files.

Comparisons between GPU passes allow a worst absolute difference of 1e-04; the measured value is reported either way.

## 🟢 No violations

## `cls_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.20e-06 |

## `cls_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 5.72e-06 |

## `cls_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 5.72e-06 |

## `cls_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.68e-06 |

## `mean_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.50e-06 |

## `mean_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.15e-06 |

## `mean_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.50e-06 |

## `mean_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.79e-06 |

## `combined`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 25600), expected (3876, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 7.63e-06 |

## `combined`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 25600), expected (2267, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.20e-06 |

## `combined`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 25600), expected (1290, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.68e-06 |

## `combined`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 25600), expected (964, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.68e-06 |

## Across tokens and versions, 30 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
| continuity with exp03 | 🟢 | worst difference 0.00e+00 against embeddings_armB_30s.npz |

## Across tokens and versions, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
| continuity with exp03 | 🟢 | worst difference 0.00e+00 against embeddings_armB_51.2s.npz |

## Across tokens and versions, 90 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
| continuity with exp03 | 🟢 | worst difference 0.00e+00 against embeddings_armB_90s.npz |

## Across tokens and versions, 120 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
| continuity with exp03 | 🟢 | worst difference 0.00e+00 against embeddings_armB_120s.npz |
