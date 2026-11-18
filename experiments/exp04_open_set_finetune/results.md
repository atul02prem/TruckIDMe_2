# exp04 — open-set driver identification with an adapted encoder

**5 partition(s) of 36 known / 10 unknown drivers**, stratified by awareness group. 51.2 s windows (2267 total, 50 channels, 512-point grid = 10.00 Hz). Encoders are fitted on the known drivers' **training** windows only, for 100 epochs; the unknown drivers are used for evaluation and nothing else. Values are mean ± sd across partitions.

`+ level` appends each window's per-channel mean and standard deviation (100 features) to the representation. Mantis divides both out at its input (`ts_scaler`), so they cannot be recovered from any embedding; this measures what that normalisation costs.

## Open set — rejecting the never-enrolled

AUROC by scoring rule; **0.500 is chance**. `window` scores one window at a time; `driver` takes the median score per driver, which is the deployment question.

| Representation | `euclidean` | `cosine` | `ratio` | `mahalanobis` | `msp` | best driver |
|---|--:|--:|--:|--:|--:|--:|
| frozen | 0.509 ± 0.030 | 0.506 ± 0.013 | 0.521 ± 0.026 | 0.514 ± 0.039 | 0.489 ± 0.023 | **0.559** (`ratio`) |
| frozen + level | 0.509 ± 0.030 | 0.506 ± 0.013 | 0.523 ± 0.028 | 0.514 ± 0.039 | 0.499 ± 0.017 | **0.557** (`mahalanobis`) |
| full | 0.510 ± 0.035 | 0.520 ± 0.024 | 0.514 ± 0.021 | 0.514 ± 0.027 | 0.498 ± 0.032 | **0.566** (`mahalanobis`) |
| full + level | 0.511 ± 0.035 | 0.522 ± 0.025 | 0.517 ± 0.022 | 0.515 ± 0.026 | 0.508 ± 0.027 | **0.566** (`mahalanobis`) |
| scratch | 0.515 ± 0.018 | 0.512 ± 0.031 | 0.508 ± 0.022 | 0.516 ± 0.012 | 0.494 ± 0.022 | **0.577** (`euclidean`) |
| scratch + level | 0.515 ± 0.019 | 0.513 ± 0.031 | 0.509 ± 0.022 | 0.516 ± 0.012 | 0.481 ± 0.021 | **0.575** (`euclidean`) |

## Closed set — naming the enrolled drivers

36-way, random floor 2.8%. Three read-outs on the same representation: `linear_probe` is the standard protocol for evaluating a learned representation, `lda_centroid` replaces PCA's unsupervised variance objective with a supervised between-driver one, and `random_forest` assumes no metric. A large spread between them means exp03's low frozen number was a **read-out** limitation rather than a representation limitation.

| Representation | linear probe | LDA + centroid | random forest |
|---|--:|--:|--:|
| frozen | **26.2%** ± 1.4% (top-2 38.4%) | **28.7%** ± 2.7% (top-2 41.2%) | **21.2%** ± 0.8% (top-2 35.1%) |
| frozen + level | **26.4%** ± 1.2% (top-2 38.8%) | **29.0%** ± 2.8% (top-2 41.4%) | **23.6%** ± 1.2% (top-2 36.7%) |
| full | **30.1%** ± 2.3% (top-2 43.9%) | **33.2%** ± 2.7% (top-2 48.2%) | **31.8%** ± 1.5% (top-2 46.7%) |
| full + level | **30.3%** ± 2.5% (top-2 43.8%) | **33.2%** ± 2.8% (top-2 48.2%) | **31.6%** ± 0.9% (top-2 47.1%) |
| scratch | **19.3%** ± 0.6% (top-2 32.0%) | **19.2%** ± 1.1% (top-2 31.2%) | **24.4%** ± 1.3% (top-2 37.9%) |
| scratch + level | **19.2%** ± 1.0% (top-2 32.1%) | **19.3%** ± 1.3% (top-2 31.7%) | **25.4%** ± 0.8% (top-2 39.4%) |

## Cost

| Arm | Mean fine-tuning minutes per partition |
|---|--:|
| full | 22.1 |
| scratch | 22.1 |

## How to read this

- **`full` − `scratch`** is the value of the pre-training, with the architecture held fixed. It is the only comparison here that licenses a claim about foundation models rather than about transformers.
- **`+ level` − plain** is what instance normalisation costs. If it is large, the finding is that a shape-only encoder cannot see driver identity on this data, whatever its weights.
- **frozen** reuses exp03's embeddings unchanged, as the reference point adaptation is measured against.

## Figures

- `outputs/figures/exp04_roc.png`
- `outputs/figures/exp04_auroc_comparison.png`
- `outputs/figures/exp04_closed_set.png`

## Caveat that bounds every number

Each driver drove **once**, so an unknown driver is also an unknown *day*: a rejection may fire because the conditions are unfamiliar rather than because the person drives differently. These AUROCs are an upper bound on genuine behavioural rejection. See `DECISIONS.md` C1.

