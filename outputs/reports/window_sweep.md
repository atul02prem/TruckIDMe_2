# TruckIDMe — Driver-ID Accuracy vs. Window Duration

5-fold stratified-on-driver CV, Random Forest (300 trees), 9 aggregates per CAN signal.
Feasibility: how much driving is needed to identify a driver (random baseline = 1/46 = 2.2%).

| Window (s) | Top-1 | ± std | Top-2 | Top-5 | Windows | ~per driver |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 42.0% | 0.9% | 57.0% | 76.7% | 4292 | 93 |
| 60 | 45.8% | 2.4% | 59.8% | 78.9% | 2136 | 46 |
| 90 | 47.1% | 2.3% | 62.8% | 81.9% | 1419 | 31 |
| 120 | 49.8% | 2.4% | 64.7% | 82.6% | 1061 | 23 |
| 180 | 51.0% | 2.9% | 66.6% | 84.6% | 700 | 15 |
| 240 | 49.8% | 4.9% | 63.1% | 81.9% | 520 | 11 |
| 300 | 50.7% | 3.0% | 67.2% | 84.0% | 406 | 9 |
