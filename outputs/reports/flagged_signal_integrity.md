# Flagged-signal integrity — T1/T2/T3

46 usable drivers. Tests why the sampling QC flagged SPN 3030, 5052 (dropout) and 2979 (multi-rate). See `signal_integrity_thread.md`.

## ⚠️ Verdicts — read these first

| test | signal | verdict | evidence |
|:--:|--:|:--:|---|
| H1/T1 | 3030 | 🔴 refuted | state 0: present 97% (n=11,872,514); state 1: present 99% (n=1,059,393) |
| H2/T2 | 5052 | 🔴 refuted | state 0: present 100% (n=11,872,514); state 1: present 99% (n=1,059,393) |
| H3/T3 | 2979 | 🔴 confirmed multi-rate | 54% of Δt below the 50 Hz mode period; Δt p10/p50/p90 = 3.3/16.9/20.9 ms |

## T1/T2 detail — target presence by 573 lockup state

### H1/T1: SPN 3030 presence vs SPN 573 state

| 573 state | target present % | state samples |
|--:|--:|--:|
| 0 | 97.1% | 11,872,514 |
| 1 | 99.0% | 1,059,393 |

### H2/T2: SPN 5052 presence vs SPN 573 state

| 573 state | target present % | state samples |
|--:|--:|--:|
| 0 | 99.7% | 11,872,514 |
| 1 | 99.5% | 1,059,393 |

