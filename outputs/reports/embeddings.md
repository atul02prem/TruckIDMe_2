# Frozen Mantis embeddings

`paris-noah/Mantis-8M`, frozen (no training), on **cuda**, read out at two layers: **index 2 (block 3 of 6)**, the project's, and **final (block 6 of 6)**. Mantis numbers its 6 blocks from 0. Built by `src/features/build_embeddings.py` from the window tensors; checked by `QC/verify_embeddings.py`.

Each of the 50 channels is encoded on its own and the per-channel vectors are concatenated. `combined` is `cls_token` followed by `mean_token` for each channel, so it holds twice the numbers but is built from the same 256-wide token space.

| Layer | Token | Window | Windows | Dims/ch | Features | Features per train example | Size | Time |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| index 2 (block 3 of 6) | `cls_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 12.6 s |
| index 2 (block 3 of 6) | `cls_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 6.9 s |
| index 2 (block 3 of 6) | `cls_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 4.1 s |
| index 2 (block 3 of 6) | `cls_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 46 MB | 3.1 s |
| index 2 (block 3 of 6) | `mean_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 11.9 s |
| index 2 (block 3 of 6) | `mean_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 7.1 s |
| index 2 (block 3 of 6) | `mean_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 4.1 s |
| index 2 (block 3 of 6) | `mean_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 45 MB | 3.1 s |
| index 2 (block 3 of 6) | `combined` | 30 s | 3876 | 512 | 25,600 | **9.4** | 355 MB | 12.2 s |
| index 2 (block 3 of 6) | `combined` | 51.2 s | 2267 | 512 | 25,600 | **16.1** | 212 MB | 7.1 s |
| index 2 (block 3 of 6) | `combined` | 90 s | 1290 | 512 | 25,600 | **28.3** | 122 MB | 4.1 s |
| index 2 (block 3 of 6) | `combined` | 120 s | 964 | 512 | 25,600 | **37.9** | 91 MB | 3.1 s |
| final (block 6 of 6) | `cls_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 19.0 s |
| final (block 6 of 6) | `cls_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 11.2 s |
| final (block 6 of 6) | `cls_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 6.5 s |
| final (block 6 of 6) | `cls_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 45 MB | 4.8 s |
| final (block 6 of 6) | `mean_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 19.2 s |
| final (block 6 of 6) | `mean_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 11.2 s |
| final (block 6 of 6) | `mean_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 6.5 s |
| final (block 6 of 6) | `mean_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 46 MB | 4.8 s |
| final (block 6 of 6) | `combined` | 30 s | 3876 | 512 | 25,600 | **9.4** | 355 MB | 19.3 s |
| final (block 6 of 6) | `combined` | 51.2 s | 2267 | 512 | 25,600 | **16.1** | 212 MB | 11.2 s |
| final (block 6 of 6) | `combined` | 90 s | 1290 | 512 | 25,600 | **28.3** | 122 MB | 6.6 s |
| final (block 6 of 6) | `combined` | 120 s | 964 | 512 | 25,600 | **37.9** | 91 MB | 4.9 s |
| index 0 (block 1 of 6) | `mean_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 173 MB | 7.5 s |
| index 1 (block 2 of 6) | `mean_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 9.8 s |
| index 3 (block 4 of 6) | `mean_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 14.5 s |
| index 4 (block 5 of 6) | `mean_token` | 30 s | 3876 | 256 | 12,800 | **4.7** | 172 MB | 16.8 s |
| index 0 (block 1 of 6) | `mean_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 4.4 s |
| index 1 (block 2 of 6) | `mean_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 5.7 s |
| index 3 (block 4 of 6) | `mean_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 8.5 s |
| index 4 (block 5 of 6) | `mean_token` | 51.2 s | 2267 | 256 | 12,800 | **8.1** | 104 MB | 9.8 s |
| index 0 (block 1 of 6) | `mean_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 2.6 s |
| index 1 (block 2 of 6) | `mean_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 3.4 s |
| index 3 (block 4 of 6) | `mean_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 5.0 s |
| index 4 (block 5 of 6) | `mean_token` | 90 s | 1290 | 256 | 12,800 | **14.2** | 61 MB | 5.8 s |
| index 0 (block 1 of 6) | `mean_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 46 MB | 1.9 s |
| index 1 (block 2 of 6) | `mean_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 46 MB | 2.5 s |
| index 3 (block 4 of 6) | `mean_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 45 MB | 3.7 s |
| index 4 (block 5 of 6) | `mean_token` | 120 s | 964 | 256 | 12,800 | **19.0** | 45 MB | 4.3 s |

## Features per training example

Features divided by training windows (70% of each driver's windows under the chronological split). Every value is above 1: there are more features than training examples in every configuration, which is why every read-out downstream standardises and projects before measuring distance. `combined` doubles the ratio at every window.

Shorter windows give more examples at the same width, but those extra windows come from the same 46 drives and are correlated, so the effective sample size grows less than the count suggests.

## Which experiments read which token

| Token | Read by |
|---|---|
| `cls_token` | exp03 analysis, exp04, exp05 — chosen early in `DECISIONS.md` D10, later superseded |
| `mean_token` | exp06 onward — chosen on inner validation in exp06 |
| `combined` | exp06 token comparison only |
