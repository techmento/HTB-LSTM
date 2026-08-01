"""Loads the trained models and runs predictions on raw sensor readings.

Three prediction paths are exposed:
- predict()        -> Random Forest, single reading
- predict_lstm()    -> LSTM, sequence of the last 10 readings for one machine
- predict_hybrid()  -> average of RF and LSTM probabilities, same 10 readings
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

from app.schemas import (
    SensorReading,
    PredictionResponse,
    BatchPredictionResult,
    BatchPredictionResponse,
)

# The exact feature order both models were trained on. Any DataFrame/array we
# build for prediction must have its columns/last axis in this same order.
FEATURE_ORDER = [
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

SEQUENCE_LENGTH = 10  # must match ml/train_lstm.py

# Weight given to RF's probability in the hybrid average (LSTM gets the
# remainder). Chosen via grid search in ml/evaluate_all.py, not a plain 50/50.
HYBRID_RF_WEIGHT = 0.55

# Human-readable labels for each rule flag, shown to the dashboard user
# instead of the raw feature name.
FAULT_TYPE_LABELS = {
    "oil_pressure_fault": "Oil Pressure Anomaly",
    "oil_temp_fault": "Lubrication Oil Overheating",
    "coolant_temp_fault": "Coolant Overheating",
    "exhaust_temp_fault": "Exhaust Gas Overheating",
    "rpm_fault": "Engine/Generator Overspeed",
}

# Paths to the saved models/scaler, resolved relative to this file so it
# works regardless of the directory the server is launched from.
MODELS_DIR = Path(__file__).resolve().parent.parent / "ml" / "models"
RF_MODEL_PATH = MODELS_DIR / "rf_model.pkl"
LSTM_MODEL_PATH = MODELS_DIR / "lstm_model.keras"
LSTM_SCALER_PATH = MODELS_DIR / "lstm_scaler.pkl"

# Written by ml/evaluate_all.py: accuracy/precision/recall/f1/ROC-AUC and
# confusion matrix for RF, LSTM, and Hybrid, computed on the held-out test set.
EVALUATION_RESULTS_PATH = MODELS_DIR / "evaluation_results.json"

# Training dataset, used by get_dataset_stats() to power the dashboard's
# static summary cards (computed from this file, not from any upload).
DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "sealine_data_with_features.csv"
SENSOR_COLUMNS = [
    "Engine RPM",
    "Lub oil pressure",
    "Lub oil temperature",
    "Coolant temperature",
    "Exhaust temperature",
]

# Columns a batch upload (CSV/Excel) must have, matching the raw column
# names used in sealine_data_with_features.csv. Machine_ID (e.g. "ME1",
# "GEN2") identifies each physical machine; Machine_Category (Engine vs
# Generator) is derived from its prefix rather than required as its own
# column, so the RPM fault threshold can still be picked correctly.
REQUIRED_BATCH_COLUMNS = [
    "Machine_ID",
    "Engine RPM",
    "Lub oil pressure",
    "Lub oil temperature",
    "Coolant temperature",
    "Exhaust temperature",
]

# Loaded once when this module is first imported, and reused for every request.
rf_model = joblib.load(RF_MODEL_PATH)
lstm_model = load_model(LSTM_MODEL_PATH)
lstm_scaler = joblib.load(LSTM_SCALER_PATH)


def build_features(reading: SensorReading) -> dict:
    """Compute is_generator and the 5 rule-based flags from a raw sensor reading.

    Returns a dict with all 12 feature keys, in the order the models expect.
    """
    is_generator = 1 if reading.machine_category == "Generator" else 0

    oil_pressure_fault = 1 if (
        reading.lub_oil_pressure > 6.5 or reading.lub_oil_pressure < 2.5
    ) else 0

    oil_temp_fault = 1 if (
        reading.lub_oil_temperature > 100 or reading.lub_oil_temperature < 50
    ) else 0

    coolant_temp_fault = 1 if (
        reading.coolant_temperature > 85 or reading.coolant_temperature < 60
    ) else 0

    # Exhaust temperature can be missing (sensor unavailable). Training used
    # X.fillna(0), so a missing reading must become 0 here too, not NaN.
    exhaust_temperature = (
        reading.exhaust_temperature if reading.exhaust_temperature is not None else 0
    )

    exhaust_temp_fault = 0
    if reading.exhaust_temperature is not None and reading.exhaust_temperature > 400:
        exhaust_temp_fault = 1

    if is_generator == 0:
        rpm_fault = 1 if reading.engine_rpm > 1700 else 0
    else:
        rpm_fault = 1 if reading.engine_rpm > 1600 else 0

    num_rules_triggered = (
        oil_pressure_fault
        + oil_temp_fault
        + coolant_temp_fault
        + exhaust_temp_fault
        + rpm_fault
    )

    return {
        "Engine RPM": reading.engine_rpm,
        "Lub oil pressure": reading.lub_oil_pressure,
        "Lub oil temperature": reading.lub_oil_temperature,
        "Coolant temperature": reading.coolant_temperature,
        "Exhaust temperature": exhaust_temperature,
        "is_generator": is_generator,
        "oil_pressure_fault": oil_pressure_fault,
        "oil_temp_fault": oil_temp_fault,
        "coolant_temp_fault": coolant_temp_fault,
        "exhaust_temp_fault": exhaust_temp_fault,
        "rpm_fault": rpm_fault,
        "num_rules_triggered": num_rules_triggered,
    }


def _triggered_rules(features: dict) -> tuple[list[str], int]:
    """Names of the rule-based checks that fired, for an explainable result."""
    rule_flags = {
        "oil_pressure_fault": features["oil_pressure_fault"],
        "oil_temp_fault": features["oil_temp_fault"],
        "coolant_temp_fault": features["coolant_temp_fault"],
        "exhaust_temp_fault": features["exhaust_temp_fault"],
        "rpm_fault": features["rpm_fault"],
    }
    triggered = [name for name, flag in rule_flags.items() if flag == 1]
    return triggered, features["num_rules_triggered"]


def get_fault_types(triggered_rules: list[str]) -> list[str]:
    """Map triggered rule names to their human-readable fault type labels."""
    if not triggered_rules:
        return ["No Fault Detected"]
    return [FAULT_TYPE_LABELS[rule] for rule in triggered_rules]


def _rf_probability(features: dict) -> float:
    """Random Forest's probability of Fault for a single reading's features."""
    row = pd.DataFrame([features], columns=FEATURE_ORDER)
    # predict_proba returns [P(class 0), P(class 1)] since scikit-learn sorts
    # classes ascending; index 1 is the probability of "Fault".
    return float(rf_model.predict_proba(row)[0][1])


def _lstm_probability(readings: list[SensorReading]) -> float:
    """LSTM's probability of Fault for a sequence of exactly 10 readings."""
    if len(readings) != SEQUENCE_LENGTH:
        raise ValueError(
            f"LSTM prediction requires exactly {SEQUENCE_LENGTH} readings, got {len(readings)}"
        )

    # Build a (10, 12) array of raw features, one row per reading, in the
    # same chronological order they were given (most recent last).
    sequence = np.array(
        [[build_features(r)[col] for col in FEATURE_ORDER] for r in readings],
        dtype=float,
    )

    # Scale with the same MinMaxScaler fitted during training, then add the
    # batch dimension the model expects: (1, 10, 12).
    scaled = lstm_scaler.transform(sequence).reshape(1, SEQUENCE_LENGTH, len(FEATURE_ORDER))

    probability = lstm_model.predict(scaled, verbose=0)[0][0]
    return float(probability)


def predict(reading: SensorReading) -> PredictionResponse:
    """Random Forest prediction from a single raw sensor reading."""
    features = build_features(reading)
    fault_probability = _rf_probability(features)
    triggered_rules, num_rules_triggered = _triggered_rules(features)

    return PredictionResponse(
        status="Fault" if fault_probability >= 0.5 else "Normal",
        fault_probability=fault_probability,
        triggered_rules=triggered_rules,
        num_rules_triggered=num_rules_triggered,
        model_used="random_forest",
        fault_types=get_fault_types(triggered_rules),
    )


def predict_lstm(readings: list[SensorReading]) -> PredictionResponse:
    """LSTM prediction from the last 10 readings of one machine.

    The rule-flag info in the response (triggered_rules, num_rules_triggered)
    describes the most recent reading, since that's the one being classified.
    """
    fault_probability = _lstm_probability(readings)

    latest_features = build_features(readings[-1])
    triggered_rules, num_rules_triggered = _triggered_rules(latest_features)

    return PredictionResponse(
        status="Fault" if fault_probability >= 0.5 else "Normal",
        fault_probability=fault_probability,
        triggered_rules=triggered_rules,
        num_rules_triggered=num_rules_triggered,
        model_used="lstm",
        fault_types=get_fault_types(triggered_rules),
    )


def predict_hybrid(readings: list[SensorReading]) -> PredictionResponse:
    """Weighted average of RF (on the last reading) and LSTM (on all 10 readings).

    The 0.55/0.45 RF/LSTM weighting was chosen by a grid search over the held-out
    test set in ml/evaluate_all.py (selected for best F1-score) — not a plain
    50/50 average. If the models are retrained, re-run evaluate_all.py and
    update HYBRID_RF_WEIGHT below to match its new selected weight.
    """
    latest_features = build_features(readings[-1])
    rf_probability = _rf_probability(latest_features)
    lstm_probability = _lstm_probability(readings)

    hybrid_probability = HYBRID_RF_WEIGHT * rf_probability + (1 - HYBRID_RF_WEIGHT) * lstm_probability
    triggered_rules, num_rules_triggered = _triggered_rules(latest_features)

    return PredictionResponse(
        status="Fault" if hybrid_probability >= 0.5 else "Normal",
        fault_probability=hybrid_probability,
        triggered_rules=triggered_rules,
        num_rules_triggered=num_rules_triggered,
        model_used="hybrid",
        fault_types=get_fault_types(triggered_rules),
    )


def predict_batch(df: pd.DataFrame) -> BatchPredictionResponse:
    """Random Forest prediction for every row of an uploaded CSV/Excel file.

    Each row is turned into a SensorReading and passed through the existing
    predict() function, so the rule thresholds and RF logic are reused
    exactly as-is (no duplicated logic).
    """
    missing_columns = [col for col in REQUIRED_BATCH_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required column(s): {', '.join(missing_columns)}")

    df = df.reset_index(drop=True)

    # Date/Time are optional on a batch upload (not in REQUIRED_BATCH_COLUMNS).
    # When both are present we surface a timestamp per row so the frontend
    # can plot trends against real time instead of just row order.
    timestamps = None
    if "Date" in df.columns and "Time" in df.columns:
        timestamps = pd.to_datetime(
            df["Date"].astype(str).str[:10] + " " + df["Time"].astype(str),
            format="mixed",
            dayfirst=True,
            errors="coerce",  # unparseable rows just get no timestamp, not a crash
        )

    results: list[BatchPredictionResult] = []
    healthy_count = 0
    fault_count = 0
    by_machine: dict[str, dict[str, int]] = {}

    for row_index, row in df.iterrows():
        machine_id = str(row["Machine_ID"]).strip()
        # Engine vs Generator is inferred from the ID prefix, matching the
        # training dataset's convention (ME1, ME2 = Engine; GEN1, GEN2 = Generator).
        machine_category = "Generator" if machine_id.upper().startswith("GEN") else "Engine"

        exhaust_value = row["Exhaust temperature"]

        reading = SensorReading(
            machine_category=machine_category,
            engine_rpm=float(row["Engine RPM"]),
            lub_oil_pressure=float(row["Lub oil pressure"]),
            lub_oil_temperature=float(row["Lub oil temperature"]),
            coolant_temperature=float(row["Coolant temperature"]),
            exhaust_temperature=None if pd.isna(exhaust_value) else float(exhaust_value),
        )

        result = predict(reading)  # reuses build_features() + the RF model, no duplication

        timestamp = None
        if timestamps is not None and pd.notna(timestamps.iloc[row_index]):
            timestamp = timestamps.iloc[row_index].isoformat()

        results.append(
            BatchPredictionResult(
                row_index=row_index,
                machine_id=machine_id,
                machine_category=machine_category,
                engine_rpm=reading.engine_rpm,
                lub_oil_pressure=reading.lub_oil_pressure,
                lub_oil_temperature=reading.lub_oil_temperature,
                coolant_temperature=reading.coolant_temperature,
                exhaust_temperature=reading.exhaust_temperature,
                status=result.status,
                fault_probability=result.fault_probability,
                fault_types=result.fault_types,
                model_used=result.model_used,
                timestamp=timestamp,
            )
        )

        # Keyed by the specific machine (not just Engine/Generator) so the
        # frontend can show a per-machine breakdown, not just a category one.
        bucket = by_machine.setdefault(machine_id, {"healthy": 0, "fault": 0})
        if result.status == "Fault":
            fault_count += 1
            bucket["fault"] += 1
        else:
            healthy_count += 1
            bucket["healthy"] += 1

    total_rows = len(results)
    fault_percentage = (fault_count / total_rows * 100) if total_rows else 0.0

    summary = {
        "total_rows": total_rows,
        "healthy_count": healthy_count,
        "fault_count": fault_count,
        "fault_percentage": fault_percentage,
        "by_machine": by_machine,
    }

    return BatchPredictionResponse(results=results, summary=summary)


def get_dataset_stats() -> dict:
    """Descriptive stats, correlation matrix, and fault distribution for the
    training dataset. Powers the dashboard's static summary cards — computed
    from sealine_data_with_features.csv, not from any uploaded file.
    """
    df = pd.read_csv(DATASET_PATH)

    # numpy.float64 (what these produce) serializes to JSON fine since it
    # subclasses Python's float, so no extra conversion is needed here.
    descriptive_stats = df[SENSOR_COLUMNS].describe().to_dict()
    correlation_matrix = df[SENSOR_COLUMNS].corr().to_dict()

    fault_counts = df["Status_label"].value_counts()
    fault_distribution = {
        "Normal": int(fault_counts.get(0, 0)),
        "Fault": int(fault_counts.get(1, 0)),
    }

    return {
        "descriptive_stats": descriptive_stats,
        "correlation_matrix": correlation_matrix,
        "fault_distribution": fault_distribution,
    }


def get_model_performance() -> dict:
    """Load the RF/LSTM/Hybrid metrics + confusion matrices written by
    ml/evaluate_all.py, instead of reloading data/models to recompute them
    on every request.
    """
    if not EVALUATION_RESULTS_PATH.exists():
        raise FileNotFoundError(
            "evaluation_results.json not found — run ml/evaluate_all.py first to generate it."
        )
    with open(EVALUATION_RESULTS_PATH) as f:
        return json.load(f)
