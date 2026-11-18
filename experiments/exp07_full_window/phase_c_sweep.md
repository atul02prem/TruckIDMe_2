# exp07 Phase C — expanded open-set sweep, selected on inner validation

`full` + `mean_token`, 30 s windows, one partition. Every model is fitted on **inner-train** and scored on **inner validation**; the test period is excluded for known *and* unknown drivers, so nothing chosen here can bias Phase B's test numbers.

AUROC, **0.500 is chance**. exp04's best driver-level was **0.566**.

**Best cell: `cosine` · pca25 · l2norm_whiten · mean prototypes — driver AUROC 0.806** (window 0.589).

A maximum over 1,300 cells is optimistically biased, so the marginals below matter more than the single winner: **median** across all cells containing a level is a far more stable signal than its maximum.

## Which projection (step 2)

| Projection | median driver AUROC | best |
|---|--:|--:|
| `pca5` | 0.512 | 0.722 |
| `pca10` | 0.468 | 0.667 |
| `pca15` | 0.482 | 0.783 |
| `pca20` | 0.469 | 0.686 |
| `pca25` | 0.514 | 0.806 |
| `pca35` | 0.497 | 0.742 |
| `pca50` | 0.565 | 0.775 |
| `pca75` | 0.540 | 0.694 |
| `pca100` | 0.574 | 0.764 |
| `lda` | 0.667 | 0.806 |

## Which transform (step 3)

| Level | median driver AUROC | best |
|---|--:|--:|
| `raw` | 0.501 | 0.806 |
| `l2norm` | 0.517 | 0.783 |
| `whiten` | 0.514 | 0.792 |
| `l2norm_whiten` | 0.561 | 0.806 |
| `whiten_l2norm` | 0.539 | 0.772 |

## Which prototype (step 4)

| Level | median driver AUROC | best |
|---|--:|--:|
| `mean` | 0.571 | 0.806 |
| `median` | 0.564 | 0.772 |
| `kmeans2` | 0.539 | 0.778 |
| `kmeans3` | 0.522 | 0.806 |

## Which rule (step 5)

| Level | median driver AUROC | best |
|---|--:|--:|
| `euclidean` | 0.519 | 0.767 |
| `cosine` | 0.610 | 0.806 |
| `ratio` | 0.544 | 0.806 |
| `mahalanobis` | 0.528 | 0.772 |
| `knn1` | 0.456 | 0.667 |
| `knn5` | 0.464 | 0.711 |
| `knn10` | 0.481 | 0.719 |
| `lof` | 0.485 | 0.703 |
| `gmm` | 0.469 | 0.700 |
| `global_mahalanobis` | 0.453 | 0.619 |
| `isolation_forest` | 0.465 | 0.608 |
| `ocsvm` | 0.415 | 0.664 |
| `msp` | 0.598 | 0.743 |
| `entropy` | 0.567 | 0.753 |

## Top 15 cells

| Rule | Projection | Transform | Prototype | window | driver |
|---|---|---|---|--:|--:|
| `cosine` | pca25 | l2norm_whiten | mean | 0.589 | **0.806** |
| `ratio` | lda | raw | kmeans3 | 0.631 | **0.806** |
| `cosine` | pca25 | whiten | mean | 0.592 | **0.792** |
| `ratio` | pca15 | l2norm | kmeans3 | 0.552 | **0.783** |
| `cosine` | pca25 | whiten | kmeans2 | 0.571 | **0.778** |
| `cosine` | pca50 | l2norm_whiten | kmeans2 | 0.571 | **0.775** |
| `mahalanobis` | pca25 | whiten_l2norm | median | 0.577 | **0.772** |
| `ratio` | pca25 | whiten | median | 0.578 | **0.767** |
| `euclidean` | lda | l2norm | median | 0.622 | **0.767** |
| `cosine` | pca100 | l2norm_whiten | kmeans2 | 0.567 | **0.764** |
| `cosine` | lda | raw | kmeans3 | 0.632 | **0.761** |
| `euclidean` | lda | l2norm | kmeans2 | 0.636 | **0.758** |
| `cosine` | pca25 | raw | mean | 0.537 | **0.756** |
| `euclidean` | pca25 | whiten_l2norm | mean | 0.583 | **0.756** |
| `ratio` | lda | l2norm | median | 0.569 | **0.756** |

## Limitations

- **One partition.** Marginals are averaged over many cells, which stabilises them, but the partition itself is a single draw.
- The chosen configuration must be **re-stated on Phase B's five test partitions** before it counts as a result.
- `ocsvm`, `lof` and `gmm` hyperparameters are left at defaults.
- One drive per driver. See `DECISIONS.md` C1.
