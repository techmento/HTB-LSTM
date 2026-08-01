"""FastAPI application exposing the fault-detection model over HTTP."""

import io
from datetime import datetime, timezone

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import auth, db
from app.schemas import (
    SensorReading,
    SequenceInput,
    PredictionResponse,
    BatchPredictionResponse,
    LoginRequest,
    LoginResponse,
    SaveHistoryRequest,
    HistoryResponse,
)
from app.model import (
    predict,
    predict_lstm,
    predict_hybrid,
    predict_batch,
    get_dataset_stats,
    get_model_performance,
)

app = FastAPI(title="Ship Engine Fault Detection API")

# Allow all origins so the frontend (e.g. Vite dev server on localhost:5173)
# can call this API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    db.init_db()
    auth.seed_default_admin()


@app.get("/health")
def health():
    """Simple liveness check. Not behind auth, so it works as a basic uptime probe."""
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    """Exchanges a username/password for a session token."""
    try:
        token = auth.login(payload.username, payload.password)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))
    return LoginResponse(token=token, username=payload.username)


@app.post("/auth/logout")
def logout(user: dict = Depends(auth.get_current_user)):
    """Invalidates the caller's current session token."""
    auth.logout(user["token"])
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict_fault(reading: SensorReading, _: dict = Depends(auth.get_current_user)):
    """Random Forest prediction from a single raw sensor reading."""
    return predict(reading)


@app.post("/predict/lstm", response_model=PredictionResponse)
def predict_fault_lstm(payload: SequenceInput, _: dict = Depends(auth.get_current_user)):
    """LSTM prediction from the last 10 readings of one machine (most recent last)."""
    try:
        return predict_lstm(payload.readings)
    except ValueError as error:
        # Raised by predict_lstm() when the list isn't exactly 10 readings long.
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/predict/hybrid", response_model=PredictionResponse)
def predict_fault_hybrid(payload: SequenceInput, _: dict = Depends(auth.get_current_user)):
    """Average of RF and LSTM predictions from the last 10 readings of one machine."""
    try:
        return predict_hybrid(payload.readings)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_fault_batch(
    file: UploadFile = File(...), _: dict = Depends(auth.get_current_user)
):
    """RF prediction for every row of an uploaded CSV or Excel file of sensor readings."""
    filename = (file.filename or "").lower()
    contents = await file.read()

    # Read the upload into a DataFrame based on its file extension.
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(contents))
    else:
        raise HTTPException(status_code=400, detail="File must be a .csv or .xlsx file")

    try:
        return predict_batch(df)
    except ValueError as error:
        # Raised by predict_batch() when required columns are missing.
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/dataset/stats")
def dataset_stats(_: dict = Depends(auth.get_current_user)):
    """Descriptive stats, correlation matrix, and fault distribution for the
    training dataset. Powers the dashboard's static summary cards.
    """
    return get_dataset_stats()


@app.get("/model/performance")
def model_performance(_: dict = Depends(auth.get_current_user)):
    """Pre-computed accuracy/precision/recall/f1_score/roc_auc and confusion
    matrix for RF, LSTM, and Hybrid, as written by ml/evaluate_all.py.
    """
    try:
        return get_model_performance()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.post("/predictions/history")
def save_history(payload: SaveHistoryRequest, _: dict = Depends(auth.get_current_user)):
    """Persists prediction rows (from a manual entry or a batch upload) so
    they survive a page refresh instead of only living in browser state.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    for row in payload.rows:
        db.insert_history_row(row.model_dump(), created_at)
    return {"status": "ok", "saved": len(payload.rows)}


@app.get("/predictions/history", response_model=HistoryResponse)
def get_history(_: dict = Depends(auth.get_current_user)):
    """Returns previously saved predictions, used to rehydrate the dashboard
    on load so old results aren't lost on refresh."""
    return HistoryResponse(rows=db.get_history_rows())


@app.delete("/predictions/history")
def clear_history(_: dict = Depends(auth.get_current_user)):
    """Wipes all saved predictions — lets the user reset to a clean slate
    without needing direct database access."""
    db.clear_history_rows()
    return {"status": "ok"}
