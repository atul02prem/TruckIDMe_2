# Arm B frozen Mantis embeddings

> **SUPERSEDED by `src/features/build_embeddings.py`, which builds all three tokens at all four windows and is checked by `QC/verify_embeddings.py`. Kept runnable: its `cls_token` files are what exp03-exp05 were scored on, and the verification shows the new `cls_token` files equal them.**

Frozen encoder on **cuda**, no training. Each channel is encoded independently and the per-channel vectors concatenated.

| Window | Windows | Channels | Dims/ch | Features | Features per train example | Size | Time |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 30s | 3876 | 50 | 256 | 12800 | **4.7** | 172 MB | 13.7s |
| 51.2s | 2267 | 50 | 256 | 12800 | **8.1** | 104 MB | 6.9s |
| 90s | 1290 | 50 | 256 | 12800 | **14.2** | 61 MB | 4.1s |
| 120s | 964 | 50 | 256 | 12800 | **19.0** | 46 MB | 3.0s |

## Why the features-per-train-example column matters

It is the ratio that decides whether distance-based scoring can work at all, and it is computed against the **training** windows only (70% of each driver's, per the chronological split) rather than all of them, since the test windows are not available to fit anything. Above 1 there are more features than examples, and in high dimension Euclidean distances between all points converge toward each other — precisely the quantity nearest-centroid and KNN rely on.

Shorter windows improve the ratio by producing more windows at identical feature width, but those extra windows come from the same 46 drives and are correlated, so the *effective* sample size improves far less than the count suggests. PCA in the next step addresses the dimension directly.

