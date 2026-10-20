# TruckIDMe — CLAUDE.md
# Context and coding standards for AI-assisted development

---

## 1. PROJECT IDENTITY

Driver behavior modelling and identification using J1939 CAN bus signals
from a 2014 Kenworth T270 Class 6 truck.

Dataset: ORNL Driver Identification Dataset (50 drivers, Fort Collins CO).
A cyberattack (spoofed speedometer/tachometer → 0, dashboard warning lights)
is executed during every drive.

Three driver groups:
- G1 (17 drivers): no warning about attack
- G2 (16 drivers): warned attack may occur
- G3 (17 drivers): warned + instructed to pull over

Excluded entirely: G1S04 (low CAN sampling frequency)

Goal: identify drivers from CAN behaviour (Driver Behavior Modelling)

---

## 2. DATA FACTS — HARD WON TRUTHS, DO NOT CONTRADICT THESE
<!-- 
### GPS Timestamps
- Use `gpsTime` column — satellite-derived UTC, correct for all drivers
- DO NOT use `timestampsLocation` — this equals `canloggerTime` (local
  UTC-6 clock). It is wrong by 6 hours for normal drivers and wrong by
  2.1 YEARS for G1S10, G1S11, G1S12 (stale CANLogger clock)
- CAN timestamps (`Time{SPN}`) are on the canloggerTime clock (UTC-6)
- Solution: relative time alignment for all drivers
  t_rel = t - t_min applied separately to GPS and CAN

### G1S10, G1S11, G1S12 — Duplicate GPS Rows
- Every GPS row is written exactly twice in the SQLite database
- Appears as ~20Hz but true rate is 10Hz
- Fix: df.drop_duplicates(subset='gpsTime', inplace=True)
- After dedup these three drivers are fully usable

### GPS Frequency
- SparkFun NEO-M9N true frequency: 10Hz for ALL drivers
- After dedup: ~25,000–33,000 rows per driver (~43 min at 10Hz)

### CAN Timestamps
- Normal drivers: CAN on canloggerTime (UTC-6)
- G1S10/11/12: CAN on gpsTime (UTC) — their CANLogger clock was broken
- Relative time alignment handles both cases correctly

### CSV File Structure
- Files in data/raw_data/ are wide-format outer joins of all SQLite tables
- ~80-90% NaN is expected — each row belongs to one device only
- GPS rows: gpsTime is non-NaN, all CAN Time{SPN} are NaN
- CAN rows: Time{SPN} is non-NaN, gpsTime is NaN
- They are NOT aligned yet — that is what the pipeline does

### Excluded CAN Signals (session-identity leakage)
These SPNs must NEVER appear in any feature matrix.
They are cumulative counters that fingerprint the session, not the driver:
- 244, 245, 918  → trip/total distance (odometers)
- 182, 250       → trip/total fuel
- 247, 235, 249  → total hours, idle hours, total revolutions
- 236            → total idle fuel
- 1029, 185      → running average fuel rate/economy (encode trip history)
- 4206, 4207     → message counter/checksum (protocol metadata, no physics)
Full list always imported from src/config.py → EXCLUDE_SPNS -->

---

## 3. PIPELINE OVERVIEW

<!-- Step 1 — Build master sector map
  Input:  G1_Subject1.csv (reference driver GPS trace)
  Output: data/interim_data/master_sector_map.csv (29 sectors via RDP)
  Script: scripts/step1_build_sector_map.py

Step 2 — Merge GPS + CAN per driver
  Input:  data/raw_data/*.csv
  Output: data/interim_data/{driver_id}_merged.csv (one per driver)
  Logic:  extract gpsTime+lat+lon → dedup → relative time →
          10Hz GPS spine → bin each CAN signal onto spine
  Script: scripts/step2_merge_gps_can.py

Step 3 — Extract features per sector per driver
  Input:  data/interim_data/*_merged.csv + master_sector_map.csv
  Output: data/processed_data/feature_matrix.csv
  Script: scripts/step3_extract_features.py

Step 4 — Classification
  Input:  data/processed_data/feature_matrix.csv
  Output: outputs/reports/classification_results.csv
  Script: scripts/step4_classify.py

--- -->

## 4. CODING PRINCIPLES

### KISS — Keep It Simple
- Write the simplest code that works correctly
- No clever one-liners that need a comment to explain them
- If you need a comment to explain WHAT it does, rewrite it
- Comments explain WHY, not what

### DRY — Don't Repeat Yourself
- If logic appears twice, extract it into a function
- If a value appears twice, it belongs in config.py
- Never copy-paste code blocks
<!-- 
### Fail Fast
- Validate inputs at the TOP of every function before doing any work
- Raise specific exceptions with clear messages:
  GOOD: raise FileNotFoundError(f"Driver file not found: {path}")
  BAD:  return None  (silent failure)
- Check that output directories exist before writing, create if not -->

### One Function, One Job
- Each function does exactly one thing
- Its name is a verb that describes that one thing
- load_driver_gps() loads GPS. It does not clean or merge.
- If a function needs an "and" to describe it, split it

<!-- ### No Magic Numbers
- Every threshold, constant, or parameter lives in src/config.py
- GOOD: if len(df) < MIN_ROWS_SECTOR:
- BAD:  if len(df) < 10: -->

### Explicit Over Implicit
- Always use keyword arguments for non-obvious parameters
- Always specify dtypes when reading CSVs if known
- Always name what you're returning in complex functions

---

## 5. PYTHON CONVENTIONS

### Imports
- Standard library first, then third-party, then local
- Absolute imports only: from src.config import GPS_COL
- Never: from src.config import *

### Paths
- Use pathlib.Path everywhere — never os.path
- All base paths come from src/config.py
- GOOD: path = DATA_RAW / f"{driver_id}.csv"
- BAD:  path = "data/raw_data/" + driver_id + ".csv"

### SQL Queries (SQLite)
- Column names with spaces MUST use square brackets:
  SELECT [gpsTime], [91 Accelerator Pedal Position 1] FROM SparkfunGPSData
- Always use parameterised queries, never f-string SQL

### DataFrames
- snake_case column names after loading
- Drop NaNs explicitly — never assume a column is clean
- Use .copy() when slicing to avoid SettingWithCopyWarning
- After any groupby/merge, verify shape is what you expect

### Type Hints
- All function signatures must have type hints
- GOOD: def load_gps(driver_id: str, path: Path) -> pd.DataFrame:
- BAD:  def load_gps(driver_id, path):

### Docstrings
- Every function gets a docstring: one-line summary + Args + Returns
- Example:
  def load_gps(driver_id: str, path: Path) -> pd.DataFrame:
      """Load and deduplicate GPS data for one driver.
      
      Args:
          driver_id: e.g. 'G1_Subject1'
          path: path to the raw CSV file
          
      Returns:
          DataFrame with columns [gpsTime, latitude, longitude],
          deduplicated, sorted by gpsTime ascending.
      """

---

<!-- ## 6. WHAT NOT TO DO — EXPLICIT PROHIBITIONS

- NEVER use timestampsLocation as a timestamp for anything
- NEVER include EXCLUDE_SPNS signals in features — check against config
- NEVER hardcode a file path — always use config.py paths
- NEVER use os.path — pathlib only
- NEVER silently return None on error — always raise with a message
- NEVER use SELECT * in SQL queries — name the columns you need
- NEVER commit to main directly — use branches for experiments
- NEVER use global variables — pass arguments explicitly
- NEVER write a function longer than ~40 lines without splitting it -->

---

## 7. RESPONSE STYLE PREFERENCES

- When writing code, write the complete function — no placeholders
- If something is uncertain, say so explicitly rather than guessing
- When I ask "why", explain the reasoning not just the answer
- If you see a mistake in my approach, flag it before writing code
- Prefer showing one correct approach over listing three options
- When debugging, explain what the error means before fixing it
- Remember that you are also to function as a mentor/teacher to me teaching things i wouldn't know. Try to challenge my reasoning and though process before you proceed with giving me a plan.
