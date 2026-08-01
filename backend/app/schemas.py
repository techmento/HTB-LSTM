"""Pydantic models for request/response validation."""

from typing import Optional
from pydantic import BaseModel


class SensorReading(BaseModel):
    """Raw sensor readings sent by the client for a single prediction."""

    machine_category: str  # "Engine" or "Generator"
    engine_rpm: float
    lub_oil_pressure: float
    lub_oil_temperature: float
    coolant_temperature: float
    exhaust_temperature: Optional[float] = None  # may be missing/unavailable


class PredictionResponse(BaseModel):
    """Result returned to the client after running the model."""

    status: str  # "Normal" or "Fault"
    fault_probability: float  # probability of class 1 (Fault)
    triggered_rules: list[str]  # names of the rule-based checks that fired
    num_rules_triggered: int
    model_used: str  # "random_forest", "lstm", or "hybrid"
    fault_types: list[str]  # human-readable labels for the triggered rules


class SequenceInput(BaseModel):
    """Input for the LSTM/hybrid endpoints: the last 10 readings for one machine.

    Readings must be in chronological order, most recent last (the LSTM was
    trained to predict the status of the last reading in the sequence).
    """

    readings: list[SensorReading]


class BatchPredictionResult(BaseModel):
    """RF prediction for a single row of an uploaded batch file."""

    row_index: int
    machine_id: str
    machine_category: str  # derived from machine_id's prefix (ME* -> Engine, GEN* -> Generator)
    engine_rpm: float
    lub_oil_pressure: float
    lub_oil_temperature: float
    coolant_temperature: float
    exhaust_temperature: Optional[float]
    status: str
    fault_probability: float
    fault_types: list[str]
    model_used: str
    timestamp: Optional[str] = None  # ISO datetime, only present if the upload had Date + Time columns


class BatchPredictionResponse(BaseModel):
    """Result returned after running RF predictions over an uploaded batch file."""

    results: list[BatchPredictionResult]
    summary: dict  # total_rows, healthy_count, fault_count, fault_percentage, by_machine


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


class SaveHistoryRequest(BaseModel):
    """Rows the frontend wants persisted, in the same shape it already builds
    them (from /predict/batch results, or a manual entry's synthetic row)."""

    rows: list[BatchPredictionResult]


class HistoryRow(BatchPredictionResult):
    """A stored prediction, as returned by GET /predictions/history."""

    id: int
    created_at: str


class HistoryResponse(BaseModel):
    rows: list[HistoryRow]
