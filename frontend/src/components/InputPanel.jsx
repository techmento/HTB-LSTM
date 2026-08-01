import { useState } from "react";
import { Upload, FileSpreadsheet, Loader2, AlertCircle, Trash2 } from "lucide-react";
import Card from "./Card";
import ConfirmModal from "./ConfirmModal";
import { predictSingle, predictBatch, clearHistory } from "../api/api";

const EMPTY_FORM = {
  machine_category: "Engine",
  machine_id: "",
  date: "",
  time: "",
  engine_rpm: "",
  lub_oil_pressure: "",
  lub_oil_temperature: "",
  coolant_temperature: "",
  exhaust_temperature: "",
};

// Builds the same {results, summary} shape predict_batch() returns, but for
// a single manual reading, so the rest of the dashboard doesn't need to
// know whether the data came from a file upload or a manual entry.
function buildSingleResultPayload(reading, prediction, timestamp, machineId) {
  const isFault = prediction.status === "Fault";

  const row = {
    row_index: 0,
    machine_id: machineId,
    machine_category: reading.machine_category,
    engine_rpm: reading.engine_rpm,
    lub_oil_pressure: reading.lub_oil_pressure,
    lub_oil_temperature: reading.lub_oil_temperature,
    coolant_temperature: reading.coolant_temperature,
    exhaust_temperature: reading.exhaust_temperature,
    status: prediction.status,
    fault_probability: prediction.fault_probability,
    fault_types: prediction.fault_types,
    model_used: prediction.model_used,
    timestamp: timestamp || null,
  };

  return {
    results: [row],
    summary: {
      total_rows: 1,
      healthy_count: isFault ? 0 : 1,
      fault_count: isFault ? 1 : 0,
      fault_percentage: isFault ? 100 : 0,
      by_machine: {
        [machineId]: { healthy: isFault ? 0 : 1, fault: isFault ? 1 : 0 },
      },
    },
  };
}

export default function InputPanel({ onResults, onHistoryCleared }) {
  const [activeTab, setActiveTab] = useState("upload"); // "upload" | "manual"

  // --- Upload tab state ---
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // --- Manual entry tab state ---
  const [form, setForm] = useState(EMPTY_FORM);

  // --- Shared request state ---
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [clearing, setClearing] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  async function handleClearHistory() {
    setShowClearConfirm(false);
    setClearing(true);
    try {
      await clearHistory();
      onHistoryCleared();
    } catch {
      setError("Could not clear history. Try again.");
    } finally {
      setClearing(false);
    }
  }

  function handleFileSelect(selected) {
    if (!selected) return;
    setFile(selected);
    setError(null);
  }

  async function handleUploadSubmit(event) {
    event.preventDefault();
    if (!file) {
      setError("Please choose a CSV or XLSX file first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await predictBatch(file);
      onResults(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Batch prediction failed. Check the file and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleManualSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const reading = {
        machine_category: form.machine_category,
        engine_rpm: Number(form.engine_rpm),
        lub_oil_pressure: Number(form.lub_oil_pressure),
        lub_oil_temperature: Number(form.lub_oil_temperature),
        coolant_temperature: Number(form.coolant_temperature),
        exhaust_temperature: form.exhaust_temperature === "" ? null : Number(form.exhaust_temperature),
      };
      // Date/Time aren't part of what the RF model needs, so they're not
      // sent to /predict — they only tag the row with when it was taken.
      const timestamp = form.date && form.time ? `${form.date}T${form.time}` : null;
      // Falls back to the category itself (e.g. "Engine") if left blank, so
      // the reading still has an identifiable label without forcing an ID.
      const machineId = form.machine_id.trim() || form.machine_category;
      const prediction = await predictSingle(reading);
      onResults(buildSingleResultPayload(reading, prediction, timestamp, machineId));
    } catch (err) {
      setError(err.response?.data?.detail || "Prediction failed. Check the values and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      {/* Tab switcher */}
      <div className="flex items-center justify-between gap-2 mb-4">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("upload")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "upload"
                ? "bg-sky-50 border border-sky-200 text-sky-700"
                : "border border-transparent text-slate-400 hover:text-slate-600"
            }`}
          >
            Upload File
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("manual")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "manual"
                ? "bg-sky-50 border border-sky-200 text-sky-700"
                : "border border-transparent text-slate-400 hover:text-slate-600"
            }`}
          >
            Manual Entry
          </button>
        </div>

        <button
          type="button"
          onClick={() => setShowClearConfirm(true)}
          disabled={clearing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-600 bg-red-50 border border-red-200 hover:bg-red-100 disabled:opacity-50 transition-colors"
        >
          {clearing ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
          Clear History
        </button>
      </div>

      {showClearConfirm && (
        <ConfirmModal
          title="Delete all saved predictions?"
          message="This removes every prediction stored in history for all users. This cannot be undone."
          confirmLabel="Delete All"
          onConfirm={handleClearHistory}
          onCancel={() => setShowClearConfirm(false)}
        />
      )}

      {activeTab === "upload" ? (
        <form onSubmit={handleUploadSubmit} className="space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              handleFileSelect(e.dataTransfer.files?.[0]);
            }}
            className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-xl py-10 text-center transition-colors ${
              isDragging ? "border-sky-400 bg-sky-50" : "border-slate-300"
            }`}
          >
            {file ? (
              <>
                <FileSpreadsheet size={28} className="text-sky-600" />
                <p className="text-sm text-slate-700">{file.name}</p>
              </>
            ) : (
              <>
                <Upload size={28} className="text-slate-400" />
                <p className="text-sm text-slate-500">Drag & drop a CSV or XLSX file here</p>
              </>
            )}
            <label className="mt-2 text-xs text-sky-600 hover:text-sky-700 cursor-pointer underline underline-offset-2">
              or browse files
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files?.[0])}
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-white font-semibold text-sm py-2.5 rounded-lg transition-colors"
          >
            {loading && <Loader2 size={16} className="animate-spin" />}
            Run Batch Prediction
          </button>
        </form>
      ) : (
        <form onSubmit={handleManualSubmit} className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Field label="Machine Category">
              <select
                value={form.machine_category}
                onChange={(e) => setForm({ ...form, machine_category: e.target.value })}
                className="input"
              >
                <option value="Engine">Engine</option>
                <option value="Generator">Generator</option>
              </select>
            </Field>

            <Field label="Machine ID (optional)">
              <input
                type="text"
                placeholder="e.g. ME1, GEN2"
                value={form.machine_id}
                onChange={(e) => setForm({ ...form, machine_id: e.target.value })}
                className="input"
              />
            </Field>

            <Field label="Date (optional)">
              <input
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                className="input"
              />
            </Field>

            <Field label="Time (optional)">
              <input
                type="time"
                value={form.time}
                onChange={(e) => setForm({ ...form, time: e.target.value })}
                className="input"
              />
            </Field>

            <Field label="Engine RPM">
              <input
                type="number"
                step="any"
                required
                value={form.engine_rpm}
                onChange={(e) => setForm({ ...form, engine_rpm: e.target.value })}
                className="input"
              />
            </Field>

            <Field label="Lub Oil Pressure">
              <input
                type="number"
                step="any"
                required
                value={form.lub_oil_pressure}
                onChange={(e) => setForm({ ...form, lub_oil_pressure: e.target.value })}
                className="input"
              />
            </Field>

            <Field label="Lub Oil Temperature">
              <input
                type="number"
                step="any"
                required
                value={form.lub_oil_temperature}
                onChange={(e) => setForm({ ...form, lub_oil_temperature: e.target.value })}
                className="input"
              />
            </Field>

            <Field label="Coolant Temperature">
              <input
                type="number"
                step="any"
                required
                value={form.coolant_temperature}
                onChange={(e) => setForm({ ...form, coolant_temperature: e.target.value })}
                className="input"
              />
            </Field>

            <Field label="Exhaust Temperature (optional)">
              <input
                type="number"
                step="any"
                value={form.exhaust_temperature}
                onChange={(e) => setForm({ ...form, exhaust_temperature: e.target.value })}
                className="input"
              />
            </Field>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-white font-semibold text-sm py-2.5 rounded-lg transition-colors"
          >
            {loading && <Loader2 size={16} className="animate-spin" />}
            Run Prediction
          </button>
        </form>
      )}

      {error && (
        <div className="mt-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          <AlertCircle size={16} />
          {error}
        </div>
      )}
    </Card>
  );
}

function Field({ label, children }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-slate-500">
      {label}
      {children}
    </label>
  );
}
