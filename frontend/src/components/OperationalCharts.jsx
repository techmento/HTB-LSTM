import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Activity } from "lucide-react";
import Card from "./Card";

// One trend line per sensor, plotted across the rows of the latest batch.
// If the uploaded file had Date + Time columns, the backend attaches a
// timestamp to every row and we plot against that (real time). Otherwise we
// fall back to row_index (upload order) — the CSV/XLSX isn't guaranteed to
// have a time column at all.
const PARAMETERS = [
  { key: "engine_rpm", label: "Engine RPM", color: "#0284c7" },
  { key: "lub_oil_pressure", label: "Lub Oil Pressure", color: "#059669" },
  { key: "lub_oil_temperature", label: "Lub Oil Temperature", color: "#d97706" },
  { key: "coolant_temperature", label: "Coolant Temperature", color: "#db2777" },
  { key: "exhaust_temperature", label: "Exhaust Gas Temperature", color: "#dc2626" },
];

function formatTimestampTick(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function OperationalCharts({ results }) {
  // A manual entry always produces exactly one row, so more than one row
  // reliably means the data came from a batch upload — that's the case
  // these trend charts are actually useful for.
  const isBatch = results.length > 1;

  // Timestamps are all-or-nothing per upload (either the file had Date+Time
  // columns or it didn't), so checking the first row is enough.
  const hasTimestamps = isBatch && Boolean(results[0]?.timestamp);
  const xKey = hasTimestamps ? "timestamp" : "row_index";

  return (
    <Card title="Operational Parameters" icon={Activity}>
      {!isBatch ? (
        <div className="h-[220px] flex items-center justify-center text-sm text-slate-400 text-center px-6">
          Upload a batch file to see operational parameter trends across readings.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {PARAMETERS.map(({ key, label, color }) => (
            <MiniLineChart
              key={key}
              data={results}
              dataKey={key}
              xKey={xKey}
              isTimeAxis={hasTimestamps}
              label={label}
              color={color}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

function MiniLineChart({ data, dataKey, xKey, isTimeAxis, label, color }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
      <p className="text-xs text-slate-500 mb-2">{label}</p>
      <ResponsiveContainer width="100%" height={140}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey={xKey}
            stroke="#94a3b8"
            fontSize={10}
            tickFormatter={isTimeAxis ? formatTimestampTick : undefined}
          />
          <YAxis stroke="#94a3b8" fontSize={10} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#0f172a" }}
            labelFormatter={isTimeAxis ? formatTimestampTick : undefined}
          />
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
