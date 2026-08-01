// Thin wrapper around the FastAPI backend. All calls go straight to
// http://localhost:8000 — no routing, no proxy config.
import axios from "axios";

const API_BASE_URL = "http://localhost:8000";
const TOKEN_STORAGE_KEY = "dashboard_auth_token";

export function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function isLoggedIn() {
  return Boolean(getToken());
}

const client = axios.create({ baseURL: API_BASE_URL });

// Attach the saved session token to every request, if we have one.
client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the backend says our session is invalid/expired, drop the token and
// tell the rest of the app (App.jsx) to fall back to the login screen.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearToken();
      window.dispatchEvent(new Event("auth:logout"));
    }
    return Promise.reject(error);
  },
);

// --- Auth --------------------------------------------------------------

export async function login(username, password) {
  const response = await client.post("/auth/login", { username, password });
  setToken(response.data.token);
  return response.data;
}

export async function logout() {
  try {
    await client.post("/auth/logout");
  } finally {
    clearToken();
  }
}

// --- Predictions ---------------------------------------------------------

// Single-reading prediction (Random Forest). `reading` matches the
// SensorReading shape the backend expects.
export async function predictSingle(reading) {
  const response = await client.post("/predict", reading);
  return response.data;
}

// Batch prediction from an uploaded CSV/XLSX file.
export async function predictBatch(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await client.post("/predict/batch", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

// Descriptive stats, correlation matrix, and fault distribution computed
// once from the training dataset.
export async function getDatasetStats() {
  const response = await client.get("/dataset/stats");
  return response.data;
}

// Accuracy/precision/recall/f1/ROC-AUC + confusion matrix for RF, LSTM, and Hybrid.
export async function getModelPerformance() {
  const response = await client.get("/model/performance");
  return response.data;
}

// --- Prediction history (so results survive a page refresh) -------------

export async function saveHistory(rows) {
  const response = await client.post("/predictions/history", { rows });
  return response.data;
}

export async function getHistory() {
  const response = await client.get("/predictions/history");
  return response.data.rows;
}

export async function clearHistory() {
  const response = await client.delete("/predictions/history");
  return response.data;
}
