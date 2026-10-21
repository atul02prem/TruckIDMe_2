# Canlogger Bridge Verification Report

Excluded drivers: {'G1S11', 'G1S10', 'G1S12', 'G1S04'}

## What is measured

For every GPS row that carries both clocks:

```
offset = gpsTime - canloggerTime
```

| Column | Formula | Question it answers |
|---|---|---|
| `mean_offset_s` | `offset.mean()` | How far apart are the two clocks? |
| `std_offset_s` | `offset.std()` | Does that gap **wobble** during the drive? |
| `max_deviation_s` | `max(abs(offset - mean))` | What is the single worst excursion? |

## Findings

**1. The 21,610 s mean offset is a time zone, not an error.** It is 6 hours (21,600 s) plus a +10.1 s residual. The two clocks come from different sources:

- `gpsTime` — **satellite UTC**, an independent reference the vehicle cannot influence.
- `canloggerTime` — the **CAN logger's local clock** (Mountain Daylight Time for these drives), snapshotted into every GPS row.

Because the two differ by a whole time zone, each must be used for what it is good for: the satellite clock to *validate*, the logger clock to *align*.

**2. Our data shows a shift, not a drift.** Across all 46 drivers the offset's standard deviation is 0.023-0.045 s over a ~50-minute drive, far below the 1.0 s flag. A constant shift is harmless for alignment because it is the same correction everywhere; drift would be fatal, since a signal timestamped early in the drive would need a different correction from one timestamped late.

**3. The wobble cannot put a reading in the wrong bin.** The worst excursion anywhere is 0.098 s, while the pipeline aligns to a 10 Hz grid where one bin spans 0.100 s. Every driver's wobble is smaller than a single sample period, so no reading can be assigned to a neighbouring window.

**4. Every CAN time column lies inside the GPS-derived window.** 62 CAN `TimeXXX` columns per driver, 0 out of range (tolerance 8.0s).

## Decision reached from this QC

**`canloggerTime` is the master clock.** It is the only timestamp that speaks the CAN clock *and* is paired per-row with GPS, and this check shows it is stable enough to align on. `gpsTime` is used only to validate it — never to align, and never to validate one Teensy timestamp against another from the same device.

## Caveat

The mean offset varies *between* drivers by up to 86 s (G1S16 is the extreme), so each logger session carries its own constant bias. Harmless within a drive, where alignment needs the offset to be stable rather than identical — but it means **absolute timestamps are not comparable across drivers**. Only within-driver timing is meaningful, which is all this project uses.

## Per-driver measurements

```
        n_gps_rows  mean_offset_s  std_offset_s  max_deviation_s  n_can_time_cols  n_out_of_range out_of_range_cols
driver                                                                                                             
G1S01        26212   21607.520612      0.027922         0.058247               62               0                []
G1S13        30184   21598.712051      0.038974         0.077734               62               0                []
G1S14        27545   21605.161853      0.035380         0.069945               62               0                []
G1S15        32559   21611.986154      0.043544         0.085534               62               0                []
G1S16        25270   21685.051970      0.034474         0.068118               62               0                []
G1S17        25572   21603.660737      0.033880         0.069007               62               0                []
G1S02        29608   21606.567609      0.029927         0.059722               62               0                []
G1S03        28205   21611.166313      0.029172         0.061639               62               0                []
G1S05        28959   21608.326130      0.028440         0.063129               62               0                []
G1S06        23185   21607.374919      0.023027         0.047519               62               0                []
G1S07        26124   21608.410519      0.027819         0.057134               62               0                []
G1S08        30173   21609.444874      0.028044         0.058443               62               0                []
G1S09        25972   21607.045280      0.026676         0.056687               62               0                []
G2S01        27328   21608.092691      0.026393         0.056428               62               0                []
G2S10        25775   21612.297000      0.033202         0.070033               62               0                []
G2S11        22310   21605.241351      0.028241         0.057228               62               0                []
G2S12        25317   21604.047807      0.033364         0.068605               62               0                []
G2S13        28128   21605.568300      0.036840         0.076284               62               0                []
G2S14        27479   21608.874476      0.036426         0.084029               62               0                []
G2S15        31668   21607.296650      0.041187         0.079241               62               0                []
G2S16        24360   21615.594964      0.032276         0.062862               62               0                []
G2S02        28569   21612.786074      0.037356         0.073910               62               0                []
G2S03        25706   21608.653922      0.033074         0.065278               62               0                []
G2S04        33537   21608.604080      0.043842         0.085363               62               0                []
G2S05        26162   21607.004838      0.034173         0.075040               62               0                []
G2S06        28228   21631.210727      0.036178         0.076269               62               0                []
G2S07        33581   21603.940802      0.045470         0.097845               62               0                []
G2S08        32440   21607.286117      0.042307         0.078504               62               0                []
G2S09        25563   21607.328122      0.033709         0.067814               62               0                []
G3S01        32388   21604.790381      0.042729         0.082457               62               0                []
G3S10        27057   21606.660335      0.035345         0.072191               62               0                []
G3S11        28621   21604.432840      0.037082         0.071097               62               0                []
G3S12        28854   21607.097478      0.038476         0.086022               62               0                []
G3S13        29025   21606.693241      0.038250         0.074328               62               0                []
G3S14        26316   21607.076858      0.034621         0.069364               62               0                []
G3S15        31370   21605.522140      0.040902         0.077260               62               0                []
G3S16        26222   21610.053387      0.034278         0.069764               62               0                []
G3S17        29410   21604.431801      0.038556         0.075355               62               0                []
G3S02        32662   21618.459860      0.043591         0.086591               62               0                []
G3S03        25310   21604.733438      0.032185         0.066998               62               0                []
G3S04        28512   21605.497051      0.038035         0.080292               62               0                []
G3S05        27912   21603.580946      0.037041         0.074225               62               0                []
G3S06        29543   21604.586647      0.039765         0.086310               62               0                []
G3S07        25119   21609.083153      0.033753         0.068054               62               0                []
G3S08        32409   21627.236178      0.042231         0.079667               62               0                []
G3S09        26666   21608.823915      0.034243         0.075107               62               0                []
```
