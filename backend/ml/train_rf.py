"""Trains a Random Forest to classify a single sensor reading as Normal or Fault."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# Paths are resolved relative to this file so the script works no matter
# which directory it's launched from.
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "sealine_data_with_features.csv"
MODELS_DIR = Path(__file__).resolve().parent / "models"

# The 12 features the model is trained on, in a fixed order. app/model.py
# builds this exact same set of features (from raw sensor readings) at
# prediction time, so this order must stay in sync with that file.
FEATURE_COLUMNS = [
    "Engine RPM",
    "Lub oil pressure",
    "Lub oil temperature",
    "Coolant temperature",
    "Exhaust temperature",
    "is_generator",
    "oil_pressure_fault",
    "oil_temp_fault",
    "coolant_temp_fault",
    "exhaust_temp_fault",
    "rpm_fault",
    "num_rules_triggered",
]

TARGET_COLUMN = "Status_label"  # 0 = Normal, 1 = Fault


# --- Load data ---------------------------------------------------------------

df = pd.read_csv(DATA_PATH)

X = df[FEATURE_COLUMNS].copy()
y = df[TARGET_COLUMN]

# Missing sensor readings (e.g. Exhaust temperature when the sensor was
# unavailable) become 0. app/model.py fills missing Exhaust temperature the
# same way, so the model sees the same kind of input at prediction time.
X = X.fillna(0)


# --- Train/test split ---------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)


# --- Train the Random Forest ---------------------------------------------------

model = RandomForestClassifier(
    n_estimators=200,
    class_weight="balanced",  # Faults are rarer than Normal readings, so weight them more
    random_state=42,
)
model.fit(X_train, y_train)


# --- Evaluate on the held-out test split ----------------------------------------

y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification report:")
print(classification_report(y_test, y_pred, target_names=["Normal", "Fault"]))
print("Confusion matrix:")
print(confusion_matrix(y_test, y_pred))


# --- Save the trained model ------------------------------------------------------

MODELS_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODELS_DIR / "rf_model.pkl")
print(f"\nSaved model to {MODELS_DIR / 'rf_model.pkl'}")
