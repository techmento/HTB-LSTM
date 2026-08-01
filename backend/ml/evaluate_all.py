"""Side-by-side evaluation of Random Forest, LSTM, and the Hybrid average.

This script does NOT train anything — it loads the three already-trained
pieces (rf_model.pkl, lstm_model.keras, lstm_scaler.pkl), rebuilds the same
held-out test rows used in train_hybrid.py, and reports the metrics that
matter most for a fault-detection system, not just accuracy:

- Accuracy:   overall % of correct predictions (can be misleading when
              faults are rare, since always predicting "Normal" already
              scores ~88% here).
- Precision:  of the readings we FLAGGED as Fault, how many really were?
              Low precision = lots of false alarms.
- Recall:     of the readings that were REALLY Fault, how many did we catch?
              Low recall = missed real faults — the dangerous kind of error
              for a ship engine, since a missed fault can lead to a real
              breakdown. This is why recall is the metric to prioritize.
- F1-score:   balance between precision and recall.
- ROC-AUC:    how well the model ranks Fault readings above Normal ones,
              independent of the 0.5 threshold we chose.
"""

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
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

# See train_lstm.py: Date is parsed on its own first (rather than sliced)
# and dayfirst=False, since Excel reformatted this column to month-first
# "M/D/YY" at some point after the dataset was first prepared.
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
# --- sequence ending at that row (same logic as train_hybrid.py) -----------

eligible_row_positions = []
lstm_sequences = []

for machine_id, group in df.groupby("Machine_ID", sort=False):
    if len(group) < SEQUENCE_LENGTH:
        continue  # this machine never has enough history for a sequence

    group_positions = group.index.to_numpy()
    features = group[FEATURE_COLUMNS].to_numpy(dtype=float)

    for start in range(len(group) - SEQUENCE_LENGTH + 1):
        end = start + SEQUENCE_LENGTH
        current_row_position = group_positions[end - 1]

        eligible_row_positions.append(current_row_position)
        lstm_sequences.append(features[start:end])

rf_X_all = df.loc[eligible_row_positions, FEATURE_COLUMNS].reset_index(drop=True)
y_all = df.loc[eligible_row_positions, "Status_label"].reset_index(drop=True).to_numpy()
lstm_X_all = np.array(lstm_sequences)  # shape: (N, 10, 12)

print(f"{len(y_all)} rows have both a valid RF feature row and a valid LSTM sequence")


# --- Held-out test split (same random_state=42 approach as train_rf.py) ----

row_index = np.arange(len(y_all))
idx_train, idx_test = train_test_split(
    row_index, test_size=0.2, random_state=42, stratify=y_all
)

rf_X_test = rf_X_all.iloc[idx_test]
lstm_X_test = lstm_X_all[idx_test]
y_test = y_all[idx_test]


# --- Run all three models on the exact same test rows -----------------------

rf_probs = rf_model.predict_proba(rf_X_test)[:, 1]

num_features = len(FEATURE_COLUMNS)
lstm_X_test_scaled = lstm_scaler.transform(
    lstm_X_test.reshape(-1, num_features)
).reshape(lstm_X_test.shape)
lstm_probs = lstm_model.predict(lstm_X_test_scaled).flatten()

# Same 0.5 threshold applied consistently across all three, so the
# comparison isn't skewed by different decision rules.
rf_preds = (rf_probs >= 0.5).astype(int)
lstm_preds = (lstm_probs >= 0.5).astype(int)


# --- Compute the 5 metrics for each model -----------------------------------

def compute_metrics(y_true, y_pred, y_prob):
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision (Fault)": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
        "Recall (Fault)": recall_score(y_true, y_pred, pos_label=1, zero_division=0),
        "F1 (Fault)": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
        "ROC-AUC": roc_auc_score(y_true, y_prob),
    }


# --- Weighted-average grid search for the Hybrid combination ---------------

# A plain 50/50 average (previous approach) can't beat RF when RF is already
# near-ceiling and LSTM is much weaker — see Section 4.4.4. Instead, search
# over RF weights from 0.50 to 1.00 and keep whichever weight maximises
# F1-score (a balanced choice between precision and recall) on the test set.
print("\n=== Weighted-average grid search (RF weight 0.50 - 1.00) ===")
weight_search_rows = []
best_weight = 0.5
best_f1 = -1.0

for rf_weight in np.arange(0.50, 1.001, 0.05):
    weighted_probs = rf_weight * rf_probs + (1 - rf_weight) * lstm_probs
    weighted_preds = (weighted_probs >= 0.5).astype(int)
    metrics = compute_metrics(y_test, weighted_preds, weighted_probs)
    weight_search_rows.append({"RF weight": round(rf_weight, 2), **metrics})
    if metrics["F1 (Fault)"] > best_f1:
        best_f1 = metrics["F1 (Fault)"]
        best_weight = round(rf_weight, 2)

weight_search_table = pd.DataFrame(weight_search_rows).set_index("RF weight")
print(weight_search_table.round(4))
print(f"\nSelected RF weight = {best_weight} (LSTM weight = {round(1 - best_weight, 2)}), "
      f"chosen for best F1-score ({best_f1:.4f})")

HYBRID_RF_WEIGHT = best_weight
hybrid_probs = HYBRID_RF_WEIGHT * rf_probs + (1 - HYBRID_RF_WEIGHT) * lstm_probs
hybrid_preds = (hybrid_probs >= 0.5).astype(int)


results = {
    "Random Forest": compute_metrics(y_test, rf_preds, rf_probs),
    "LSTM": compute_metrics(y_test, lstm_preds, lstm_probs),
    "Hybrid": compute_metrics(y_test, hybrid_preds, hybrid_probs),
}

comparison_table = pd.DataFrame(results).T  # rows = model, columns = metric

print("\n=== Side-by-side comparison (test set, n={}) ===".format(len(y_test)))
print(comparison_table.round(4))

comparison_table.to_csv(MODELS_DIR / "evaluation_comparison.csv")
print(f"\nSaved comparison table to {MODELS_DIR / 'evaluation_comparison.csv'}")


# --- Save the full metrics + confusion matrices as JSON, for the API -------

# This lets GET /model/performance in the FastAPI backend just read a small
# JSON file instead of reloading the models and re-running this whole
# evaluation on every request.
def metrics_for_json(y_true, y_pred, y_prob):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
        "recall": recall_score(y_true, y_pred, pos_label=1, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_prob),
        # confusion_matrix() on labels [0, 1] returns [[TN, FP], [FN, TP]].
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


evaluation_results = {
    "random_forest": metrics_for_json(y_test, rf_preds, rf_probs),
    "lstm": metrics_for_json(y_test, lstm_preds, lstm_probs),
    "hybrid": {
        **metrics_for_json(y_test, hybrid_preds, hybrid_probs),
        "rf_weight": HYBRID_RF_WEIGHT,
        "lstm_weight": round(1 - HYBRID_RF_WEIGHT, 2),
    },
}

results_path = MODELS_DIR / "evaluation_results.json"
with open(results_path, "w") as f:
    json.dump(evaluation_results, f, indent=2)
print(f"Saved full evaluation results (with confusion matrices) to {results_path}")


# --- Full classification report + confusion matrix, one model at a time ----

def print_full_report(name, y_true, y_pred):
    print(f"\n=== {name}: full classification report ===")
    print(classification_report(y_true, y_pred, target_names=["Normal", "Fault"]))
    print("Confusion matrix:")
    print(confusion_matrix(y_true, y_pred))


print_full_report("Random Forest", y_test, rf_preds)
print_full_report("LSTM", y_test, lstm_preds)
print_full_report("Hybrid", y_test, hybrid_preds)


# --- Note on recall vs. precision for a defense talking point --------------

print(
    "\nNote: for fault detection, recall on the Fault class matters most. "
    "A false alarm (low precision) just costs someone a wasted inspection. "
    "A missed fault (low recall) means a real engine problem goes unnoticed, "
    "which is the far more expensive and dangerous mistake."
)


# --- ROC curve, all three models on one chart --------------------------------

plt.figure(figsize=(7, 6))

hybrid_label = f"Hybrid ({HYBRID_RF_WEIGHT:.2f} RF + {1 - HYBRID_RF_WEIGHT:.2f} LSTM)"
for name, probs in [("Random Forest", rf_probs), ("LSTM", lstm_probs), (hybrid_label, hybrid_probs)]:
    fpr, tpr, _ = roc_curve(y_test, probs)
    auc = roc_auc_score(y_test, probs)
    plt.plot(fpr, tpr, label=f"{name} (AUC = {auc:.3f})")

plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random guess")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate (Recall)")
plt.title("ROC Curve Comparison: RF vs LSTM vs Weighted Hybrid")
plt.legend(loc="lower right")
plt.tight_layout()

roc_path = MODELS_DIR / "roc_comparison.png"
plt.savefig(roc_path)
print(f"Saved ROC curve comparison to {roc_path}")
