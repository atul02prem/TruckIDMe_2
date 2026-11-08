# TruckIDMe — Excluded-SPN Verification (driver separability)

For each excluded SPN, η² = fraction of the signal's variance explained
by driver identity, computed across all usable drivers' raw values.
High η² confirms the signal fingerprints the trip (exclusion justified);
low η² flags a signal that overlaps across drivers (behavioural).

| SPN | Signal | η² | Verdict |
|---|---|---:|---|
| 235 | `235 Engine Total Idle Hours` | 1.000 | STRONG LEAK — exclusion well justified |
| 182 | `182 Engine Trip Fuel` | 1.000 | STRONG LEAK — exclusion well justified |
| 250 | `250 Engine Total Fuel Used` | 1.000 | STRONG LEAK — exclusion well justified |
| 918 | `918 Trip Distance (High Resolution)` | 1.000 | STRONG LEAK — exclusion well justified |
| 244 | `244 Trip Distance` | 1.000 | STRONG LEAK — exclusion well justified |
| 245 | `245 Total Vehicle Distance` | 1.000 | STRONG LEAK — exclusion well justified |
| 249 | `249 Engine Total Revolutions` | 1.000 | STRONG LEAK — exclusion well justified |
| 247 | `247 Engine Total Hours of Operation` | 1.000 | STRONG LEAK — exclusion well justified |
| 236 | `236 Engine Total Idle Fuel Used` | 1.000 | STRONG LEAK — exclusion well justified |
| 185 | `185 Engine Average Fuel Economy` | 0.999 | STRONG LEAK — exclusion well justified |
| 1029 | `1029 Trip Average Fuel Rate` | 0.999 | STRONG LEAK — exclusion well justified |
| 1761 | `1761 Aftertreatment 1 Diesel Exhaust Fluid Tank Volume` | 0.998 | STRONG LEAK — exclusion well justified |
| 96 | `96 Fuel Level 1` | 0.998 | STRONG LEAK — exclusion well justified |
| 3031 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | 0.986 | STRONG LEAK — exclusion well justified |
| 171 | `171 Ambient Air Temperature` | 0.968 | STRONG LEAK — exclusion well justified |
| 5466 | `5466 Aftertreatment 1 Diesel Particulate Filter Soot Load Regeneration Threshold` | 0.948 | STRONG LEAK — exclusion well justified |
| 1172 | `1172 Engine Turbocharger 1 Compressor Intake Temperature` | 0.941 | STRONG LEAK — exclusion well justified |
| 3721 | `3721 Aftertreatment 1 Diesel Particulate Filter Time Since Last Active Regeneration` | 0.937 | STRONG LEAK — exclusion well justified |
| 108 | `108 Barometric Pressure` | 0.743 | SUBSTANTIAL separation — exclusion defensible |
| 105 | `105 Engine Intake Manifold 1 Temperature` | 0.731 | SUBSTANTIAL separation — exclusion defensible |
| 1136 | `1136 Engine ECU Temperature` | 0.569 | SUBSTANTIAL separation — exclusion defensible |
| 177 | `177 Transmission Oil Temperature 1` | 0.378 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 975 | `975 Engine Fan 1 Estimated Percent Speed` | 0.319 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 168 | `168 Battery Potential / Power Input 1` | 0.239 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 3246 | `3246 Aftertreatment 1 Diesel Particulate Filter Outlet Temperature` | 0.166 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 3242 | `3242 Aftertreatment 1 Diesel Particulate Filter Intake Temperature` | 0.164 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 5862 | `5862 Aftertreatment 1 SCR Intermediate Temperature` | 0.142 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 4360 | `4360 Aftertreatment 1 SCR Intake Temperature` | 0.142 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 412 | `412 Engine Exhaust Gas Recirculation 1 Temperature` | 0.136 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 4363 | `4363 Aftertreatment 1 SCR Outlet Temperature` | 0.127 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 986 | `986 Engine Fan 1 Requested Percent Speed` | 0.100 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 4765 | `4765 Aftertreatment 1 Diesel Oxidation Catalyst Intake Temperature` | 0.088 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 3241 | `3241 Aftertreatment 1 Exhaust Temperature 1` | 0.088 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 110 | `110 Engine Coolant Temperature` | 0.078 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 898 | `898 Engine Requested Speed/Speed Limit` | 0.010 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 518 | `518 Engine Requested Torque/Torque Limit` | 0.003 | OVERLAPPING — behavioural, RECONSIDER excluding |
| 3544 | `3544 Time Remaining in Engine Operating State` | — | n/a (constant / single driver) |
| 4191 | `4191 Engine Requested Torque (Fractional)` | — | n/a (constant / single driver) |
| 4206 | `4206 Message Counter` | — | n/a (constant / single driver) |
| 4207 | `4207 Message Checksum` | — | n/a (constant / single driver) |
