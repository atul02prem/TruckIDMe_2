# exp08 — fine-tuned read-out block: 1 vs 3, inner validation

Round 1's protocol: inner validation (the training windows split again), one 36/10 partition, `mean_token`, `np.interp`, 60 epochs. Closed set is the best of probe / LDA / forest, 36-way; open set is inner driver AUROC under exp07's pre-registered scoring. No test window is read.

**Rule, fixed before the block-1 run:** move the fine-tuned arm to block 1 only if it beats block 3 by ≥ 2pp at ≥ 3 of 4 windows.

## Fine-tuned arm (decides)

| Window | training windows | block 3 | block 1 | difference | driver AUROC, block 3 → block 1 |
|--:|--:|--:|--:|--:|--:|
| 30 s | 1,462 | 47.8% | 34.7% | -13.1pp | 0.678 → 0.558 |
| 51.2 s | 840 | 39.9% | 44.2% | +4.4pp | 0.717 → 0.675 |
| 90 s | 462 | 45.0% | 45.5% | +0.5pp | 0.506 → 0.544 |
| 120 s | 341 | 38.4% | 45.7% | +7.2pp | 0.722 → 0.700 |

## Frozen versus fine-tuned at the same block and window

What fine-tuning adds, read on the same split (closed set, best read-out):

| Window | training windows | block 3: frozen → fine-tuned | block 1: frozen → fine-tuned |
|--:|--:|--:|--:|
| 30 s | 1,462 | 29.9% → 47.8% (+17.9pp) | 34.5% → 34.7% (+0.2pp) |
| 51.2 s | 840 | 37.4% → 39.9% (+2.5pp) | 39.9% → 44.2% (+4.4pp) |
| 90 s | 462 | 43.4% → 45.0% (+1.6pp) | 49.2% → 45.5% (-3.7pp) |
| 120 s | 341 | 42.0% → 38.4% (-3.6pp) | 46.4% → 45.7% (-0.7pp) |

## Decision

Block 1 beats block 3 by ≥ 2pp at 2 of 4 windows (51.2 s, 120 s).

**The rule is not met: the fine-tuned arm stays at block 3, 30 s.** `block1_test.py` was written in advance and is not run.

Fine-tuning helps most where training windows are most plentiful (30 s at block 3) and can hurt where they are fewest (90–120 s), consistent with updating all parameters on too little data. Not tested further here.

## Limitations

- One partition, as in Round 1; one partition varies by roughly ±3pp closed set.
- One seed.
