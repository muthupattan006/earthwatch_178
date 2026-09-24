from pathlib import Path


# ============================================================
# EARTHWATCH VISUALIZATION CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# INPUT DATA
# ============================================================

DATA_DIR = BASE_DIR / "data"

VALIDATED_DATA_PATH = DATA_DIR / "validated_data.csv"

# ============================================================
# TREND ANALYSIS DATA
# ============================================================

TREND_DATA_PATH = Path(
    r"C:\Users\Priyadharshini\Downloads\SAC_WRF_FCST_5KM_20260914.csv"
)

# ============================================================
# OUTPUT
# ============================================================

VISUAL_OUTPUT = BASE_DIR / "output"

SUMMARY_REPORT = VISUAL_OUTPUT / "summary_report.txt"



# Create output directory if it doesn't exist
VISUAL_OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)
