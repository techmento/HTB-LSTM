"""Trains an LSTM to detect faults from short sequences of sensor readings.

Unlike the Random Forest (which looks at one reading at a time), this model
looks at the last 10 readings for a single machine and predicts whether the
10th (most recent) reading is a Fault (1) or Normal (0). This lets the model
pick up on trends leading up to a fault, not just a single snapshot.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential

# Paths are resolved relative to this file so the script works no matter
# which directory it's launched from.
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "sealine_data_with_features.csv"
MODELS_DIR = Path(__file__).resolve().parent / "models"

# Same 12 features the Random Forest uses, in a fixed order (order matters
# for the DataFrame -> numpy conversion below).
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

SEQUENCE_LENGTH = 10  # number of past readings the LSTM looks at per prediction


# --- Step 1: Load the CSV and sort by Machine_ID, then Date + Time ---------

df = pd.read_csv(DATA_PATH)

# "Date" and "Time" are separate columns; combine them into one sortable
# timestamp per row. The raw Date column mixes formats (ISO
# "2025-04-10 00:00:00", legacy "14/10/2025", and Excel-reformatted
# "4/10/25 0:00") and its own embedded time is always a "0:00" placeholder —
# the real time of day lives in the separate Time column. We can't just slice
# the first 10 characters off Date (that truncates mid-value for the shorter
# Excel format), so Date is parsed on its own first, then just its date part
# is recombined with Time. dayfirst=False because cross-checking against the
# original unreformatted data confirmed Excel wrote these as month-first
# (US-style) — e.g. "4/10/25" is April 10th, not October 4th.
date_only = pd.to_datetime(df["Date"], format="mixed", dayfirst=False, errors="coerce")
df["DateTime"] = pd.to_datetime(
    date_only.dt.strftime("%Y-%m-%d") + " " + df["Time"].astype(str),
    format="mixed",
    errors="coerce",  # a handful of rows have typo'd years (e.g. "18/10/2925"); these become NaT
)

# Drop rows whose date genuinely couldn't be parsed — we can't place them
# correctly in a machine's chronological sequence, so keeping them would
# risk corrupting the sliding windows built below.
unparseable = df["DateTime"].isna().sum()
if unparseable:
    print(f"Dropping {unparseable} row(s) with unparseable Date values")
    df = df.dropna(subset=["DateTime"])

# Any missing sensor readings (e.g. Exhaust temperature) become 0, exactly
# like the fillna(0) used when training the Random Forest.
df[FEATURE_COLUMNS] = df[FEATURE_COLUMNS].fillna(0)

df = df.sort_values(["Machine_ID", "DateTime"]).reset_index(drop=True)


# --- Step 2: Build sliding-window sequences, one machine at a time ---------

# A sequence must only ever contain readings from a single machine, so we
# group by Machine_ID first and slide the window inside each group only.
sequences = []
targets = []

for machine_id, group in df.groupby("Machine_ID", sort=False):
    if len(group) < SEQUENCE_LENGTH:
        continue  # not enough history for this machine to form even one sequence

    features = group[FEATURE_COLUMNS].to_numpy(dtype=float)
    labels = group["Status_label"].to_numpy()

    # Slide a window of size 10 across this machine's readings, one step at
    # a time. The label for each window is the Status_label of its LAST
    # (10th) reading — i.e. "is the machine faulty right now, given its
    # last 10 readings?".
    for start in range(len(group) - SEQUENCE_LENGTH + 1):
        end = start + SEQUENCE_LENGTH
        sequences.append(features[start:end])
        targets.append(labels[end - 1])

X = np.array(sequences)  # shape: (num_sequences, 10, 12)
y = np.array(targets)  # shape: (num_sequences,)

print(f"Built {len(X)} sequences of length {SEQUENCE_LENGTH} from {df['Machine_ID'].nunique()} machine groups")


# --- Step 4: Train/test split (done before scaling, see note below) -------

# We split BEFORE scaling so the scaler only ever sees training data. If we
# scaled first, statistics from the test set would leak into training.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# --- Step 3: Scale features with MinMaxScaler, fit on training data only --

num_features = len(FEATURE_COLUMNS)

scaler = MinMaxScaler()
# Flatten to 2D (rows = every timestep of every training sequence) so the
# scaler can compute one min/max per feature, then reshape back to 3D.
X_train_scaled = scaler.fit_transform(X_train.reshape(-1, num_features)).reshape(X_train.shape)
X_test_scaled = scaler.transform(X_test.reshape(-1, num_features)).reshape(X_test.shape)

MODELS_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(scaler, MODELS_DIR / "lstm_scaler.pkl")


# --- Step 5: Build the LSTM model -------------------------------------------

model = Sequential([
    LSTM(64, input_shape=(SEQUENCE_LENGTH, num_features)),
    Dropout(0.3),  # randomly drops 30% of connections during training to reduce overfitting
    Dense(16, activation="relu"),
    Dense(1, activation="sigmoid"),  # single output between 0 and 1 = P(Fault)
])

# --- Step 6: Compile the model ---------------------------------------------

model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
model.summary()

# Faults are much rarer than Normal readings. class_weight makes the model
# pay more attention to the minority (Fault) class instead of just always
# predicting "Normal" to get a high accuracy score.
class_weight_values = compute_class_weight(
    class_weight="balanced", classes=np.unique(y_train), y=y_train
)
class_weight = dict(enumerate(class_weight_values))
print("Class weights:", class_weight)


# --- Step 7: Train with early stopping --------------------------------------

# Stops training once val_loss stops improving for 5 epochs in a row, and
# restores the weights from the best epoch (instead of the last one).
early_stopping = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)

history = model.fit(
    X_train_scaled,
    y_train,
    validation_split=0.2,  # carve out 20% of the training set for validation
    epochs=30,
    batch_size=32,
    class_weight=class_weight,
    callbacks=[early_stopping],
)


# --- Step 8: Evaluate on the held-out test split ----------------------------

y_pred_proba = model.predict(X_test_scaled)
y_pred = (y_pred_proba > 0.5).astype(int).flatten()

print("\n--- Test set evaluation ---")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification report:")
print(classification_report(y_test, y_pred, target_names=["Normal", "Fault"]))
print("Confusion matrix:")
print(confusion_matrix(y_test, y_pred))


# --- Step 9: Save the trained model -----------------------------------------

model.save(MODELS_DIR / "lstm_model.keras")
print(f"\nSaved model to {MODELS_DIR / 'lstm_model.keras'}")
print(f"Saved scaler to {MODELS_DIR / 'lstm_scaler.pkl'}")
