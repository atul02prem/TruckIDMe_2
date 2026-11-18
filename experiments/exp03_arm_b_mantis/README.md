# exp03 — what did the frozen Mantis encoder encode?

## Objective

The first look at Mantis on this data. Before training anything, ask what the
pre-trained encoder already puts in its embeddings, in four questions where each
one gates the next:

1. **Does the embedding space separate drivers at all?** η² per embedding
   dimension, with driver as the group.
2. **Or does it separate trip phase instead?** Early-drive windows might cluster
   together because the truck warms up and the route changes, whoever is driving.
   The same η² is computed against trip phase and awareness group on identical
   embeddings. If phase separates better than driver, any accuracy is an
   artefact.
3. **Can a driver be named from a window?** Each driver's early windows are
   averaged into one prototype; each late window goes to the nearest prototype.
4. **Is the dimensionality defeating us?** PCA to k dimensions, with k swept on
   an inner split rather than assumed.

## Inputs

Both are committed artefacts with their own verification; this experiment
builds neither.

| Input | Built by | Verified by |
|---|---|---|
| window tensors, 50 channels, 4 lengths | `src/features/build_tensors.py` | `QC/verify_tensors.py` |
| frozen embeddings, `cls_token` | `src/features/build_embeddings.py` | `QC/verify_embeddings.py` |

## Data lineage

| Stage | What | Shape |
|---|---|---|
| frozen embeddings | Mantis-8M, block index 2, `cls_token`, 50 channels × 256 | (n, 12,800); n = 3,876 / 2,267 / 1,290 / 964 |
| split | per-driver chronological: first 70% train, 5% gap, last 25% test | e.g. 1,567 / 585 at 51.2 s |
| scaling | `StandardScaler`, fitted on training windows | unchanged |
| projection | PCA to k, fitted on training windows; k chosen on an inner split | (n, k), k = 100–400 |
| read-out | nearest driver prototype, and 1-NN / 5-NN | 46 classes, chance 2.17% |

## Configuration

| | |
|---|---|
| Encoder | `paris-noah/Mantis-8M`, frozen, read-out at block index 2 (the output after block 3 of 6; Mantis counts from 0) |
| Output token | `cls_token` (see below) |
| Channels | 50; each encoded on its own, then concatenated |
| Window lengths | 30 / 51.2 / 90 / 120 s |
| Drivers | 46 |
| Seed | 42 |

**Why `cls_token`.** It was the token in use when this ran, chosen in
`DECISIONS.md` D10 with a nearest-centroid read-out on an earlier 62-channel
configuration. exp06 later re-tested the choice properly and replaced it with
`mean_token`, which wins at every window. The numbers here are the starting
point of the project, not its headline.

## Results (`embedding_analysis.md`)

### Drivers, not trip phase

| Window | η² driver, mean | η² phase, mean | ratio | dims > 0.10: driver / phase |
|--:|--:|--:|--:|--:|
| 30 s | 0.0388 | 0.0094 | 4.1× | 471 / 5 |
| 51.2 s | 0.0568 | 0.0131 | 4.3× | 1,226 / 26 |
| 90 s | 0.0849 | 0.0192 | 4.4× | 3,348 / 144 |
| 120 s | 0.1074 | 0.0267 | 4.0× | 5,999 / 437 |

🟢 **Driver separates about 4× more strongly than trip phase at every window
length**, and awareness group separates least of all. A frozen encoder that was
never told about drivers places their windows apart, and not merely by where in
the drive a window falls.

### Naming a driver: weak, but above chance

| Window | Nearest prototype top-1 | top-5 | 1-NN |
|--:|--:|--:|--:|
| 30 s | 7.4% | 28.1% | 7.2% |
| **51.2 s** | **10.6%** | 30.9% | 8.9% |
| 90 s | 8.9% | 29.8% | 6.0% |
| 120 s | 10.2% | 29.3% | 9.4% |

Chance is 2.17%. The separation that η² finds does not turn into much accuracy
under a nearest-prototype read-out. Later experiments show the read-out was the
limit, not the embeddings: on these **identical** 51.2 s embeddings, LDA reaches
23.2% (exp05).

### Dimensionality: accuracy rises with k

On the inner split, accuracy rises with k at every window and is best at k =
100 (30 s) or 400 (the others). By the reading set out in advance, a rising
curve means the information is spread thinly across many dimensions and PCA
discards it, rather than distances collapsing in high dimension.

### What this experiment establishes

- The frozen encoder carries driver information, ahead of trip phase.
- A nearest-prototype read-out uses little of it: 10.6% at best. This is the
  first rung of the project's results; the read-out (exp04, exp05), output token
  (exp06) and fine-tuning (exp07) each move it up.

## Files

| File | What |
|---|---|
| `analyse_embeddings.py` → `embedding_analysis.md` | the four questions above |
| `outputs/figures/armB_tsne_driver_*.png`, `armB_tsne_phase_*.png` | t-SNE of the same points, coloured by driver and by trip phase |
| `embed.py` → `embeddings.md` | **superseded** by `src/features/build_embeddings.py`; kept runnable as the original build of the `cls_token` files |

## Commands

```bash
python -m src.features.build_tensors             # if the tensors are missing
python -m src.features.build_embeddings          # if the embeddings are missing
python -u -m experiments.exp03_arm_b_mantis.analyse_embeddings
```

## Limitations

- **`cls_token`**, later superseded by `mean_token` (exp06).
- **Nearest-prototype read-out only**, which later experiments show understates
  these embeddings by more than half.
- **The inner split for k draws on the same 46 drives**, so its windows are
  correlated with the outer training windows; k is less independently chosen
  than the window count suggests.
- **Resampling is linear interpolation** — accepted for all 50 channels with the
  measurements in `DECISIONS.md` S5.
- **One drive per driver.** The chronological split separates early from late
  within a single trip, not across sessions. See `DECISIONS.md` C1.
