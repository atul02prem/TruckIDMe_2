# TruckIDMe — Per-Tick Driver-ID Baseline (no Stage-2 aggregation)

Each row = ONE 100 ms tick. Features = instantaneous CAN channel values.
No temporal context — a deliberate LOWER BOUND vs the windowed result.

**Channels (features):** 142 (mean-downsampled 10 Hz)
**Split:** per-driver chronological — train first 70% of each drive, 5% gap discarded, test last 25%. Train and test cover different route positions (prevents temporal-adjacency leakage; model must fingerprint behaviour, not memorise position).
**Train rows:** 905,161   **Test rows:** 323,295   (every 1th tick)
**Drivers:** 46   **Random baseline:** 2.2%

| Metric | Accuracy |
|---|---:|
| top-1 | 16.8% |
| top-2 | 26.8% |
| top-5 | 44.9% |

## Interpretation
Compare against the windowed result (9 aggregates over 120 s windows). The
gap quantifies the value of temporal aggregation: how much driver identity
lives in *how signals evolve over time* vs their instantaneous values.
