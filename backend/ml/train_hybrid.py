"""Combines the trained Random Forest and LSTM models into a simple hybrid.

This script does NOT train anything new — it loads the two already-trained
models (see train_rf.py and train_lstm.py), runs both on the same rows, and
averages their fault probabilities together. The point is to see whether
combining a "single reading" model (RF) with a "recent trend" model (LSTM)
beats either one alone.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import load_model

# Paths are resolved relative to this file so the script works no matter
# which directory it's launched from.
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "sealine_data_with_features.csv"
MODELS_DIR = Path(__file__).resolve().parent / "models"

# Must exactly match the feature list/order used in train_rf.py and train_lstm.py.
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

SEQUENCE_LENGTH = 10  # must match train_lstm.py


# --- Load the already-trained models ----------------------------------------

rf_model = joblib.load(MODELS_DIR / "rf_model.pkl")
lstm_model = load_model(MODELS_DIR / "lstm_model.keras")
lstm_scaler = joblib.load(MODELS_DIR / "lstm_scaler.pkl")


# --- Load data and rebuild features, same as train_rf.py / train_lstm.py ----

df = pd.read_csv(DATA_PATH)
# See train_lstm.py for why Date is parsed on its own first (rather than
# sliced) and why dayfirst=False (Excel reformatted this column to
# month-first "M/D/YY" at some point after the dataset was first prepared).
date_only = pd.to_datetime(df["Date"], format="mixed", dayfirst=False, errors="coerce")
df["DateTime"] = pd.to_datetime(
    date_only.dt.strftime("%Y-%m-%d") + " " + df["Time"].astype(str),
    format="mixed",
    errors="coerce",
)
unparseable = df["DateTime"].isna().sum()
if unparseable:
    print(f"Dropping {unparseable} row(s) with unparseable Date values")
    df = df.dropna(subset=["DateTime"])

df[FEATURE_COLUMNS] = df[FEATURE_COLUMNS].fillna(0)
df = df.sort_values(["Machine_ID", "DateTime"]).reset_index(drop=True)


# --- Find rows that have BOTH a valid RF feature row and a valid LSTM ------
# --- sequence ending at that row (i.e. the row has >= 9 readings before it --
# --- for the same machine) --------------------------------------------------

# Every row has a valid RF feature row on its own. A row only has a valid
# LSTM sequence if it's at least the 10th reading of its Machine_ID group.
# So "eligible" rows are exactly the rows the LSTM's sliding window in
# train_lstm.py would have produced a sequence for.
eligible_row_positions = []
lstm_sequences = []

for machine_id, group in df.groupby("Machine_ID", sort=False):
    if len(group) < SEQUENCE_LENGTH:
        continue  # this machine never has enough history for a sequence

    group_positions = group.index.to_numpy()  # positions in the sorted df
    features = group[FEATURE_COLUMNS].to_numpy(dtype=float)

    for start in range(len(group) - SEQUENCE_LENGTH + 1):
        end = start + SEQUENCE_LENGTH
        current_row_position = group_positions[end - 1]  # the row the sequence "ends" at

        eligible_row_positions.append(current_row_position)
        lstm_sequences.append(features[start:end])

# RF features and labels for the eligible rows only, aligned by position
# (0..N-1) with lstm_sequences below.
rf_X_all = df.loc[eligible_row_positions, FEATURE_COLUMNS].reset_index(drop=True)
y_all = df.loc[eligible_row_positions, "Status_label"].reset_index(drop=True).to_numpy()
lstm_X_all = np.array(lstm_sequences)  # shape: (N, 10, 12)

print(f"{len(y_all)} rows have both a valid RF feature row and a valid LSTM sequence")


# --- Split into train/test and keep only the test rows -----------------------

# We don't retrain anything here, so idx_train is discarded — we only need
# a held-out test set to fairly compare all three approaches on the same
# rows. Note: this is a fresh split over the "eligible rows" subset, not the
# exact same test split used inside train_rf.py or train_lstm.py, because
# those two scripts had different eligible rows (RF used every row, LSTM
# only rows with a full 10-reading history).
row_index = np.arange(len(y_all))
idx_train, idx_test = train_test_split(
    row_index, test_size=0.2, random_state=42, stratify=y_all
)

rf_X_test = rf_X_all.iloc[idx_test]
lstm_X_test = lstm_X_all[idx_test]
y_test = y_all[idx_test]


# --- Step 1: RF predicted probability of Fault -------------------------------

rf_probs = rf_model.predict_proba(rf_X_test)[:, 1]
rf_preds = rf_model.predict(rf_X_test)


# --- Step 2: LSTM predicted probability of Fault ------------------------------

num_features = len(FEATURE_COLUMNS)
lstm_X_test_scaled = lstm_scaler.transform(
    lstm_X_test.reshape(-1, num_features)
).reshape(lstm_X_test.shape)

lstm_probs = lstm_model.predict(lstm_X_test_scaled).flatten()
lstm_preds = (lstm_probs >= 0.5).astype(int)


# --- Step 3 & 4: Average the two probabilities and threshold at 0.5 ---------

hybrid_probs = (rf_probs + lstm_probs) / 2
hybrid_preds = (hybrid_probs >= 0.5).astype(int)


# --- Evaluate all three approaches on the exact same test rows --------------

def print_report(name, y_true, y_pred):
    print(f"\n=== {name} ===")
    print("Accuracy:", accuracy_score(y_true, y_pred))
    print(classification_report(y_true, y_pred, target_names=["Normal", "Fault"]))
    print("Confusion matrix:")
    print(confusion_matrix(y_true, y_pred))


print_report("Random Forest alone", y_test, rf_preds)
print_report("LSTM alone", y_test, lstm_preds)
print_report("Hybrid (average of RF and LSTM probabilities)", y_test, hybrid_preds)
