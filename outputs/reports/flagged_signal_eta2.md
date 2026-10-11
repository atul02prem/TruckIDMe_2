# T4 — η² of the flagged signals (value separability)

Do 3030 / 5052 / 2979 leak driver identity through their *values*? η² = between-driver variance / total. Calibrated by anchors: behavioural mean η² ≈ **0.014** (91/84/190), leak anchor η² ≈ **1.000** (245).

## ⚠️ Verdicts — read these first

| suspect | Signal | η² | verdict |
|--:|---|--:|:--|
| 2979 | 2979 Vehicle Acceleration Rate Limit Status | 0.000 | 🟢 behavioural → keep |
| 5052 | 5052 Transmission Clutch/Converter Input Spe | 0.016 | 🟢 behavioural → keep |
| 3030 | 3030 Transmission Torque Converter Ratio | 0.023 | 🟢 behavioural → keep |

## Context — all η² ranked (suspects + anchors)

| η² | role | SPN | Signal |
|--:|:--|--:|---|
| 1.000 | leak anchor | 245 | 245 Total Vehicle Distance |
| 0.023 | 🎯 suspect | 3030 | 3030 Transmission Torque Converter Ratio |
| 0.018 | behavioural anchor | 84 | 84 Wheel-Based Vehicle Speed |
| 0.016 | 🎯 suspect | 5052 | 5052 Transmission Clutch/Converter Input Spe |
| 0.014 | behavioural anchor | 190 | 190 Engine Speed |
| 0.009 | behavioural anchor | 91 | 91 Accelerator Pedal Position 1 |
| 0.000 | 🎯 suspect | 2979 | 2979 Vehicle Acceleration Rate Limit Status |

Thresholds: η² ≥ 0.9 (or ≈ leak anchor) → exclude; η² ≤ 0.5 (or ≈ behavioural anchor) → keep; else judgment.
