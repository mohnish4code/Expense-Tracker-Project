from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "datasets"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"

TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"
BUDGET_CSV = DATA_DIR / "budget.csv"

ANOMALY_MODEL = "anomaly"
OVERSPEND_MODEL = "overspend"

# fixed rate used for the whole dataset, see README limitations
TND_TO_INR = 29
SEED = 42

CATEGORIES = [
    "Food & Groceries",
    "Transport",
    "Restaurants & Cafés",
    "Health & Wellness",
    "Education & Self-Dev",
    "Personal Care",
    "Entertainment & Leisure",
    "Shopping & Clothing",
    "Gifts & Social",
    "Travel & Holidays",
    "Rent",
    "Utilities",
    "Subscriptions & Digital",
    "Savings & Investment",
]

PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "Bank Transfer"]
