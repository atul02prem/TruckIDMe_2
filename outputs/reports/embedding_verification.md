# Embedding verification — do the frozen embeddings match their source?

Reads the 24 files written by `src/features/build_embeddings.py` (2 layers x 3 tokens x 4 window lengths) and checks them against the window tensors, against each other, and against exp03's earlier `cls_token` files.

Comparisons between GPU passes allow a worst absolute difference of 1e-04; the measured value is reported either way.

## 🟢 No violations

## index 2 (block 3 of 6), `cls_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.20e-06 |

## index 2 (block 3 of 6), `cls_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 5.72e-06 |

## index 2 (block 3 of 6), `cls_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 5.72e-06 |

## index 2 (block 3 of 6), `cls_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.68e-06 |

## index 2 (block 3 of 6), `mean_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.50e-06 |

## index 2 (block 3 of 6), `mean_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.15e-06 |

## index 2 (block 3 of 6), `mean_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.50e-06 |

## index 2 (block 3 of 6), `mean_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.79e-06 |

## index 2 (block 3 of 6), `combined`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 25600), expected (3876, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 7.63e-06 |

## index 2 (block 3 of 6), `combined`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 25600), expected (2267, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.20e-06 |

## index 2 (block 3 of 6), `combined`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 25600), expected (1290, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.68e-06 |

## index 2 (block 3 of 6), `combined`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 25600), expected (964, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer 2 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.68e-06 |

## final (block 6 of 6), `cls_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.34e-05 |

## final (block 6 of 6), `cls_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.24e-05 |

## final (block 6 of 6), `cls_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.34e-05 |

## final (block 6 of 6), `cls_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | cls_token, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.34e-05 |

## final (block 6 of 6), `mean_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 8.34e-06 |

## final (block 6 of 6), `mean_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 8.58e-06 |

## final (block 6 of 6), `mean_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 9.54e-06 |

## final (block 6 of 6), `mean_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 7.63e-06 |

## final (block 6 of 6), `combined`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 25600), expected (3876, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.24e-05 |

## final (block 6 of 6), `combined`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 25600), expected (2267, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.43e-05 |

## final (block 6 of 6), `combined`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 25600), expected (1290, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.34e-05 |

## final (block 6 of 6), `combined`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 25600), expected (964, 25600) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | combined, layer -1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.72e-05 |

## layer profile: index 0 (block 1 of 6), `mean_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 0 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.26e-06 |

## layer profile: index 0 (block 1 of 6), `mean_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 0 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.50e-06 |

## layer profile: index 0 (block 1 of 6), `mean_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 0 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.86e-06 |

## layer profile: index 0 (block 1 of 6), `mean_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 0 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.03e-06 |

## layer profile: index 1 (block 2 of 6), `mean_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.26e-06 |

## layer profile: index 1 (block 2 of 6), `mean_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.26e-06 |

## layer profile: index 1 (block 2 of 6), `mean_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.26e-06 |

## layer profile: index 1 (block 2 of 6), `mean_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 1 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.50e-06 |

## layer profile: index 3 (block 4 of 6), `mean_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 3 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 1.91e-06 |

## layer profile: index 3 (block 4 of 6), `mean_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 3 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.86e-06 |

## layer profile: index 3 (block 4 of 6), `mean_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 3 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.03e-06 |

## layer profile: index 3 (block 4 of 6), `mean_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 3 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 2.03e-06 |

## layer profile: index 4 (block 5 of 6), `mean_token`, 30 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (3876, 12800), expected (3876, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 4 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 7.03e-06 |

## layer profile: index 4 (block 5 of 6), `mean_token`, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (2267, 12800), expected (2267, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 4 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 6.68e-06 |

## layer profile: index 4 (block 5 of 6), `mean_token`, 90 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (1290, 12800), expected (1290, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 4 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 5.72e-06 |

## layer profile: index 4 (block 5 of 6), `mean_token`, 120 s

| Check | Result | Detail |
|---|:-:|---|
| shape | 🟢 | (964, 12800), expected (964, 12800) |
| all finite | 🟢 | 0 non-finite values |
| labels match the tensor | 🟢 | driver, start_time and channels identical |
| stored token and layer | 🟢 | mean_token, layer 4 |
| reproducible | 🟢 | 64 windows re-embedded, worst difference 7.63e-06 |

## index 2 (block 3 of 6), across tokens, 30 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
| continuity with exp03 | 🟢 | worst difference 0.00e+00 against embeddings_armB_30s.npz |

## index 2 (block 3 of 6), across tokens, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
| continuity with exp03 | 🟢 | worst difference 0.00e+00 against embeddings_armB_51.2s.npz |

## index 2 (block 3 of 6), across tokens, 90 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
| continuity with exp03 | 🟢 | worst difference 0.00e+00 against embeddings_armB_90s.npz |

## index 2 (block 3 of 6), across tokens, 120 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
| continuity with exp03 | 🟢 | worst difference 0.00e+00 against embeddings_armB_120s.npz |

## final (block 6 of 6), across tokens, 30 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |

## final (block 6 of 6), across tokens, 51.2 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |

## final (block 6 of 6), across tokens, 90 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |

## final (block 6 of 6), across tokens, 120 s

| Check | Result | Detail |
|---|:-:|---|
| combined = cls_token then mean_token, per channel | 🟢 | worst absolute difference 0.00e+00 |
