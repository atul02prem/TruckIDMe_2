# exp01 results — driver ID from native slow signals (<= 5 Hz, no resampling)

11 signals, native samples, mean, median, std, min, max, p10, p90, dmean, dstd per signal per window.
Per-driver chronological split (train 70% / gap 5% / test 25%). Random baseline = 2.2% (1/46).

| Window (s) | Top-1 | Top-2 | Top-5 | Features | Train win | Test win |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 13.9% | 23.3% | 42.9% | 99 | 2978 | 1088 |
| 60 | 15.0% | 25.5% | 43.5% | 99 | 1473 | 552 |
| 90 | 18.8% | 29.3% | 47.0% | 99 | 971 | 368 |
| 120 | 14.5% | 25.1% | 42.8% | 99 | 715 | 283 |
