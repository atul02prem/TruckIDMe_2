# src/config.py

from pathlib import Path

# ─────────────────────────────────────────────────────────
# PROJECT ROOT (Pathlib Path object)
# ─────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent

print(f"Project root found at: {ROOT}") #Project root found at: /home/ap9107/TruckIDMe
# ─────────────────────────────────────────────────────────
# DATA PATHS (Pathlib Path objects)
# ─────────────────────────────────────────────────────────
DATA_RAW       = ROOT / "data" / "raw_data"        # csv files
DATA_INTERIM   = ROOT / "data" / "interim_data"    # GPS+CAN merged per driver
DATA_PROCESSED = ROOT / "data" / "processed_data"  # Feature matrices
DATA_EXTERNAL  = ROOT / "data" / "external_data"   # Any external data (e.g. weather, maps)
# ─────────────────────────────────────────────────────────
# OUTPUT PATHS
# ─────────────────────────────────────────────────────────
OUT_MODELS  = ROOT / "outputs" / "models"
OUT_FIGURES = ROOT / "outputs" / "figures"
OUT_REPORTS = ROOT / "outputs" / "reports"

# # ─────────────────────────────────────────────────────────
# # GPS / ALIGNMENT SETTINGS
# # ─────────────────────────────────────────────────────────
# GPS_HZ       = 10       # SparkFun NEO-M9N true frequency
# BIN_SIZE_S   = 0.1      # 0.1s bins = 10Hz grid
# GPS_COL      = "gpsTime"           # satellite UTC — NOT timestampsLocation
# LAT_COL      = "latitude"
# LON_COL      = "longitude"

# # Drivers whose GPS rows are duplicated — need deduplication
# DUPLICATE_GPS_DRIVERS = {"G1S10", "G1S11", "G1S12"}

# ─────────────────────────────────────────────────────────
# DRIVERS TO EXCLUDE ENTIRELY
# ─────────────────────────────────────────────────────────
EXCLUDE_DRIVERS = {
    "G1S04",  # low CAN sampling frequency
    "G1S10",  # canloggerTime defaulted to 2022-05-01 (no Teensy RTC sync) + duplicate GPS rows
    "G1S11",  # canloggerTime defaulted to 2022-05-01 (no Teensy RTC sync) + duplicate GPS rows
    "G1S12",  # canloggerTime defaulted to 2022-05-01 (no Teensy RTC sync) + duplicate GPS rows
}

# ─────────────────────────────────────────────────────────
# CAN SIGNAL EXCLUSIONS
# cumulative / metadata / session-leakage signals
# ─────────────────────────────────────────────────────────
# MINIMAL exclusion set for the Stage-1 leakage-audit loop.
# Only unambiguous leaks (η² ≥ 0.99) are excluded a priori; every other signal
# is re-introduced and the audit loop removes any that reveal themselves as
# leaks in the top feature importances. See outputs/reports/research_plan.md
# and outputs/reports/excluded_spn_verification.md.
EXCLUDE_SPNS = {
    # ── Leaks, η² ≥ 0.99 (verified trip fingerprints) ────────
    #    Cumulative counters (η² = 1.000)
    245,    # Total Vehicle Distance
    244,    # Trip Distance
    918,    # Trip Distance High Resolution
    250,    # Engine Total Fuel Used
    182,    # Engine Trip Fuel
    247,    # Engine Total Hours of Operation
    235,    # Engine Total Idle Hours
    249,    # Engine Total Revolutions
    236,    # Engine Total Idle Fuel Used
    #    Running averages (η² = 0.999)
    185,    # Engine Average Fuel Economy
    1029,   # Trip Average Fuel Rate
    #    Trip-state levels (η² = 0.998)
    96,     # Fuel Level 1
    1761,   # DEF Tank Volume
    # ── Held out for DATA QUALITY, not leakage ───────────────
    #    Bursty: ~92% null, ffill produces stale values (revisit w/ active flag)
    898,    # Engine Requested Speed/Speed Limit
    518,    # Engine Requested Torque/Torque Limit
    4191,   # Engine Requested Torque (Fractional)
    3544,   # Time Remaining in Engine Operating State
    #    Protocol constants (zero variance, no behaviour)
    4206,   # Message Counter
    4207,   # Message Checksum
    # ── Audit iter 1: top importances, η² ≥ 0.9 (trip artifacts) ──
    3721,   # DPF Time Since Last Active Regeneration (η²=0.937)
    5466,   # DPF Soot Load Regeneration Threshold    (η²=0.948)
    3031,   # DEF Tank Temperature                     (η²=0.986)
    171,    # Ambient Air Temperature                  (η²=0.968)
    1172,   # Turbocharger 1 Compressor Intake Temp    (η²=0.941)
    # ── Audit iter 2: thermal / ambient / electrical STATE family ──
    # Not driver behaviour — proxy trip timing (each subject drove a distinct
    # day). All temperatures + barometric + battery + thermal-mgmt fans.
    # Pressures tied to driver actions (brake, boost, fuel rail) are KEPT.
    105,    # Engine Intake Manifold 1 Temperature
    110,    # Engine Coolant Temperature
    177,    # Transmission Oil Temperature 1
    412,    # EGR 1 Temperature
    1136,   # Engine ECU Temperature
    3241,   # Aftertreatment Exhaust Temperature 1
    3242,   # DPF Intake Temperature
    3246,   # DPF Outlet Temperature
    4360,   # SCR Intake Temperature
    4363,   # SCR Outlet Temperature
    4765,   # DOC Intake Temperature
    5862,   # SCR Intermediate Temperature
    108,    # Barometric Pressure (ambient)
    168,    # Battery Potential / Power Input 1 (electrical)
    975,    # Engine Fan 1 Estimated Percent Speed
    986,    # Engine Fan 1 Requested Percent Speed
    # #------ added by me after reviewing drop.py list given by ORNL
    # 100, # Engine Oil Pressure
    # 4816, 
    # 908,
    # 1087,
    # 518,
    # 1242,
    # 101,
    # 907,
    # 185,
    # 1088,
    # 3246,
    # 412,
    # 3246,
    # 1136,
    # 908,
    # 1242,
    # 412,
    # 1717,
    # 91,
    # 236,
    # 5862,
    # 5466,
    # 2945,
    # 4154,
    # 190,
    # 105,
    # 907,
    # 4207,
    # 92,
    # 918,
    # 168,
    # 4206,
    # 975,
    # 4363,
    # 512,
    # 986,
    # 3721,
    # 3357,
    # 518,
    # 641,
    # 3231,
    # 184,
    # 3251,
    # 3229,
    # 244,
    # 3216,
    # 1717,
    # 904,
    # 574,
    # 110,
    # 247,
    # 3544,
    # 513,
    # 171,
    # 5398,
    # 3216,
    # 1172,
    # 2978,
    # 177,
    # 514,
    # 2432,
    # 526,
    # 1029,
    # 574,
    # 641,
    # 526,
    # 641,
    # 110,
    # 182,
    # 161,
    # 3239,
    # 117,
    # 110,
    # 105,
    # 3242,
    # 1088,
    # 512,
    # 412,
    # 1172,
    # 3229,
    # 515,
    # 177,
    # 92,
    # 108,
    # 118,
    # 526,
    # 108,
    # 184,
    # 132,
    # 157,
    # 523,
    # 906,
    # 157,
    # 3230,
    # 513,
    # 1172,
    # 117,
    # 100,
    # 3232,
    # 573,
    # 523,
    # 4206,
    # 1209,
    # 5052,
    # 1136,
    # 132,
    # 247,
    # 4765,
    # 191,
    # 1209,
    # 524,
    # 5862,
    # 2659,
    # 4207,
    # 3031,
    # 3544,
    # 905,
    # 986,
    # 3241,
    # 904,
    # 3239,
    # 574,
    # 92,
    # 177,
    # 3610,
    # 512,
    # 1242,
    # 245,
    # 250,
    # 905,
    # 907,
    # 27,
    # 2659,
    # 3030,
    # 4207,
    # 3357,
    # 986,
    # 1087,
    # 3226,
    # 907,
    # 4154,
    # 171,
    # 101,
    # 96,
    # 3242,
    # 184,
    # 3610,
    # 247,
    # 1209,
    # 3251,
    # 102,
    # 84,
    # 103,
    # 573,
    # 3226,
    # 3544,
    # 5313,
    # 5015, 
    # 3030,
    # 523,
    # 244,
    # 51,
    # 524,
    # 1761,
    # 2432,
    # 3241,
    # 5862,
    # 96,
    # 5398,
    # 5015,
    # 524,
    # 27,
    # 3230,
    # 512,
    # 1087,
    # 1029,
    # 3241,
    # 906,
    # 244,
    # 3721,
    # 3216,
    # 4154,
    # 3232,
    # 3216,
    # 3231,
    # 2945,
    # 4816,
    # 3031,
    # 1761,
    # 3251,
    # 5466,
    # 3721,
    # 171,
    # 1136,
    # 975,
    # 986,
    # 132,
    # 105,
    # 1172,
    # 2978,
    # 245,
    # 177, 
    # 918 
}

# # ─────────────────────────────────────────────────────────
# # ROUTE / SECTOR SETTINGS
# # ─────────────────────────────────────────────────────────
# REFERENCE_DRIVER  = "G1S01"   # GPS trace used to build master sector map
# N_SECTORS         = 29        # RDP output sectors
# RDP_EPSILON_M     = 20.0      # RDP simplification threshold in metres

# # ─────────────────────────────────────────────────────────
# # FEATURE EXTRACTION
# # ─────────────────────────────────────────────────────────
# WINDOW_S          = 30        # classification window in seconds
# STRIDE_S          = 15        # 50% overlap
# MIN_ROWS_SECTOR   = 10        # minimum GPS rows to compute sector features

# # ─────────────────────────────────────────────────────────
# # MODEL TRAINING
# # ─────────────────────────────────────────────────────────
# SEED              = 42
# N_FOLDS           = 5
# TEST_SIZE         = 0.2

# # ─────────────────────────────────────────────────────────
# # CYBERATTACK
# # ─────────────────────────────────────────────────────────
# ATTACK_DURATION_S = 60        # max attack duration
# # Group labels
# GROUP_NO_WARNING   = "G1"
# GROUP_WARNING      = "G2"
# GROUP_PULLOVER     = "G3"