# exp07 Phase C final — open-set on test, pre-registered configuration

`full` + `mean_token`, 30 s windows, 5 partitions of 36 known / 10 unknown drivers. Everything is fitted on known-train only; unknown drivers appear once, at scoring. **0.500 is chance.**

The configuration on the first row was fixed from inner-validation **medians** before any test window was scored, and is reported whatever it achieved. Later rows are context, including the configuration whose test-split maximum was 0.806 on one partition.

| Configuration | projection | transform | rule | window AUROC | driver AUROC |
|---|---|---|---|--:|--:|
| **pre-registered** | lda | l2norm_whiten | `cosine` | 0.585 ± 0.025 | **0.689** ± 0.043 |
| exp04 default | pca50 | raw | `mahalanobis` | 0.511 ± 0.029 | 0.514 ± 0.062 |
| exp04 default, cosine | pca50 | raw | `cosine` | 0.543 ± 0.035 | 0.623 ± 0.074 |
| best inner-val cell | pca25 | l2norm_whiten | `cosine` | 0.528 ± 0.028 | 0.549 ± 0.075 |
| lda + raw + cosine | lda | raw | `cosine` | 0.622 ± 0.028 | 0.724 ± 0.062 |
| lda + l2norm + euclidean | lda | l2norm | `euclidean` | 0.624 ± 0.028 | 0.729 ± 0.064 |

## Reference points

| | window AUROC | driver AUROC |
|---|--:|--:|
| exp04 `full` (`cls_token`, 51.2 s, PCA 50, raw) | 0.514 | 0.566 |
| exp04 `scratch` (random initialisation) | 0.516 | 0.577 |
| chance | 0.500 | 0.500 |

## How much to trust each column

- **Window-level** compares ~585 known against ~149 unknown windows per partition. Stable; small differences are meaningful.
- **Driver-level** compares 36 known against 10 unknown — 46 points. Simulated single-partition sd is **0.08–0.10**, so the ± column here is the honest measure of what one partition can tell you. This is the deployment-relevant metric but the noisier one.

## Limitations

- **One drive per driver**, so an unknown driver is also an unknown day: any positive AUROC conflates 'new person' with 'new conditions'. This bounds every number above. See `DECISIONS.md` C1.
- The LDA projection is fitted on the 36 known drivers, so its directions are chosen to separate *those* drivers. That it still helps reject unseen ones is the result, not an assumption.
- Resampling is `np.interp`, which aliases on downsample. At 30 s the grid is 17.07 Hz, the least affected of the four window lengths.
- Fixed 60-epoch budget, final epoch, no model selection.
