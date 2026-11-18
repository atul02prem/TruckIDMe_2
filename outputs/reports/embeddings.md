# Frozen Mantis embeddings

`paris-noah/Mantis-8M`, read-out layer **2**, frozen (no training), on **cuda**. Built by `src/features/build_embeddings.py` from the window tensors; checked by `QC/verify_embeddings.py`.

Each of the 50 channels is encoded on its own and the per-channel vectors are concatenated. `combined` is `cls_token` followed by `mean_token` for each channel, so it holds twice the numbers but is built from the same 256-wide token space.

| Token | Window | Windows | Dims/ch | Features | Features per train example | Size | Time |
|---|--:|--:|--:|--:|--:|--:|--:|
| `cls_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 26.0 s |
| `cls_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 14.7 s |
| `cls_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 8.5 s |
| `cls_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 46 MB | 6.3 s |
| `mean_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 25.2 s |
| `mean_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 14.8 s |
| `mean_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 8.6 s |
| `mean_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 45 MB | 6.3 s |
| `combined` | 30 s | 3876 | 512 | 25,600 | **9.4** | 355 MB | 25.4 s |
| `combined` | 51.2 s | 2267 | 512 | 25,600 | **16.1** | 212 MB | 14.7 s |
| `combined` | 90 s | 1290 | 512 | 25,600 | **28.3** | 122 MB | 8.5 s |
| `combined` | 120 s | 964 | 512 | 25,600 | **37.9** | 91 MB | 6.3 s |

## Features per training example

Features divided by training windows (70% of each driver's windows under the chronological split). Every value is above 1: there are more features than training examples in every configuration, which is why every read-out downstream standardises and projects before measuring distance. `combined` doubles the ratio at every window.

Shorter windows give more examples at the same width, but those extra windows come from the same 46 drives and are correlated, so the effective sample size grows less than the count suggests.

## Which experiments read which token

| Token | Read by |
|---|---|
| `cls_token` | exp03 analysis, exp04, exp05 — chosen early in `DECISIONS.md` D10, later superseded |
| `mean_token` | exp06 onward — chosen on inner validation in exp06 |
| `combined` | exp06 token comparison only |
