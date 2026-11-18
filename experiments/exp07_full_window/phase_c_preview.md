# exp07 Phase C — exhaustive open-set scoring sweep

**PREVIEW — one partition, encoder fitted on inner-train.** Used to decide whether any rule escapes the ~0.51 ceiling before spending GPU time. Not reportable.

AUROC, **0.500 is chance**. exp04 reached **0.514** using prototype rules only. Driver-level takes the median score per driver.

**Best cell: `mahalanobis`, PCA 25, l2norm — driver AUROC 0.714** (window 0.570).

## PCA 25

| Rule | raw window / driver | l2norm window / driver | whiten window / driver |
|---|--:|--:|--:|
| *prototype (exp04 used only these)* | | | |
| `euclidean` | 0.518 / 0.472 | 0.549 / **0.644** | 0.522 / 0.489 |
| `cosine` | 0.562 / **0.667** | 0.547 / **0.647** | 0.564 / **0.700** |
| `ratio` | 0.537 / 0.581 | 0.534 / **0.614** | 0.552 / **0.694** |
| `mahalanobis` | 0.527 / 0.497 | 0.570 / **0.714** | 0.527 / 0.497 |
| *neighbour* | | | |
| `knn1` | 0.520 / 0.494 | 0.498 / 0.497 | 0.525 / 0.450 |
| `knn5` | 0.502 / 0.458 | 0.491 / 0.494 | 0.510 / 0.467 |
| `knn10` | 0.522 / 0.472 | 0.489 / 0.453 | 0.536 / 0.494 |
| *local density* | | | |
| `lof` | 0.480 / 0.383 | 0.452 / 0.336 | 0.519 / 0.472 |
| *global density* | | | |
| `gmm` | 0.515 / 0.364 | 0.484 / 0.356 | 0.507 / 0.356 |
| `global_mahalanobis` | 0.518 / 0.456 | 0.549 / **0.611** | 0.518 / 0.456 |
| *boundary* | | | |
| `isolation_forest` | 0.523 / 0.475 | 0.537 / 0.564 | 0.524 / 0.469 |
| `ocsvm` | 0.514 / 0.464 | 0.518 / 0.544 | 0.524 / 0.503 |
| *classifier* | | | |
| `msp` | 0.513 / 0.592 | 0.500 / 0.475 | 0.515 / 0.565 |
| `entropy` | 0.503 / 0.511 | 0.506 / 0.528 | 0.505 / 0.514 |

## PCA 50

| Rule | raw window / driver | l2norm window / driver | whiten window / driver |
|---|--:|--:|--:|
| *prototype (exp04 used only these)* | | | |
| `euclidean` | 0.514 / 0.492 | 0.559 / **0.658** | 0.522 / 0.564 |
| `cosine` | 0.554 / **0.633** | 0.559 / **0.653** | 0.553 / **0.600** |
| `ratio` | 0.534 / 0.572 | 0.531 / 0.508 | 0.538 / 0.472 |
| `mahalanobis` | 0.530 / 0.542 | 0.560 / **0.600** | 0.530 / 0.542 |
| *neighbour* | | | |
| `knn1` | 0.533 / 0.586 | 0.502 / 0.533 | 0.512 / 0.519 |
| `knn5` | 0.513 / 0.517 | 0.492 / 0.489 | 0.518 / 0.494 |
| `knn10` | 0.530 / 0.478 | 0.492 / 0.447 | 0.525 / 0.483 |
| *local density* | | | |
| `lof` | 0.484 / 0.375 | 0.464 / 0.367 | 0.494 / 0.428 |
| *global density* | | | |
| `gmm` | 0.507 / 0.483 | 0.487 / 0.372 | 0.515 / 0.428 |
| `global_mahalanobis` | 0.509 / 0.558 | 0.528 / 0.556 | 0.509 / 0.558 |
| *boundary* | | | |
| `isolation_forest` | 0.517 / 0.522 | 0.504 / 0.572 | 0.517 / 0.522 |
| `ocsvm` | 0.509 / 0.397 | 0.510 / 0.519 | 0.513 / 0.508 |
| *classifier* | | | |
| `msp` | 0.521 / 0.579 | 0.518 / 0.561 | 0.521 / 0.585 |
| `entropy` | 0.517 / 0.547 | 0.522 / 0.558 | 0.517 / 0.553 |

## PCA 100

| Rule | raw window / driver | l2norm window / driver | whiten window / driver |
|---|--:|--:|--:|
| *prototype (exp04 used only these)* | | | |
| `euclidean` | 0.520 / 0.517 | 0.576 / **0.653** | 0.534 / 0.544 |
| `cosine` | 0.562 / **0.656** | 0.574 / **0.653** | 0.589 / **0.714** |
| `ratio` | 0.557 / **0.647** | 0.548 / **0.639** | 0.551 / **0.672** |
| `mahalanobis` | 0.536 / 0.503 | 0.570 / 0.586 | 0.536 / 0.503 |
| *neighbour* | | | |
| `knn1` | 0.534 / 0.542 | 0.496 / 0.467 | 0.517 / 0.450 |
| `knn5` | 0.523 / 0.508 | 0.492 / 0.439 | 0.527 / 0.464 |
| `knn10` | 0.531 / 0.494 | 0.493 / 0.458 | 0.524 / 0.425 |
| *local density* | | | |
| `lof` | 0.494 / 0.378 | 0.454 / 0.322 | 0.522 / 0.411 |
| *global density* | | | |
| `gmm` | 0.523 / 0.497 | 0.492 / 0.475 | 0.513 / 0.514 |
| `global_mahalanobis` | 0.519 / 0.489 | 0.549 / 0.542 | 0.519 / 0.489 |
| *boundary* | | | |
| `isolation_forest` | 0.543 / 0.572 | 0.513 / 0.525 | 0.543 / 0.572 |
| `ocsvm` | 0.510 / 0.403 | 0.534 / **0.642** | 0.525 / 0.494 |
| *classifier* | | | |
| `msp` | 0.504 / 0.511 | 0.525 / **0.621** | 0.509 / 0.519 |
| `entropy` | 0.522 / 0.550 | 0.530 / 0.597 | 0.523 / 0.569 |

## How to read this

- **The prototype family is exp04's control.** If those land near 0.51 again, this pipeline agrees with exp04 and anything above is a real gain rather than a coding difference.
- **Driver-level is the deployment question** — a decision is taken per driver, not per 30-second window.
- Bold marks driver AUROC >= 0.60, the threshold `exp04/STAGE2.md` pre-registered as 'real but weak signal'.
- This is a **maximum over many cells**, so the best value is optimistically biased. Any rule chosen here must be re-stated on the remaining partitions before it is reported as a result.

## Limitations

- One drive per driver: an unknown driver is also an unknown day, so any positive AUROC conflates 'new person' with 'new conditions'. See `DECISIONS.md` C1.
- `ocsvm` and `lof` have hyperparameters (`nu`, `n_neighbors`) left at sensible defaults rather than swept.
