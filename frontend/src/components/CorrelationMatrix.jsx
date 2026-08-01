import { Grid3x3 } from "lucide-react";
import Card from "./Card";
import StatusState from "./StatusState";

// Red for positive correlation, blue for negative — a classic diverging
// heatmap scale, blended over the white cell background.
function correlationColor(value) {
  const clamped = Math.max(-1, Math.min(1, value));
  return clamped >= 0
    ? `rgba(239, 68, 68, ${clamped * 0.55})` // red-500
    : `rgba(59, 130, 246, ${-clamped * 0.55})`; // blue-500
}

export default function CorrelationMatrix({ data, loading, error }) {
  const columns = data ? Object.keys(data) : [];

  return (
    <Card title="Correlation Analysis" icon={Grid3x3}>
      <StatusState loading={loading} error={error} />
      {!loading && !error && data && (
        <div className="overflow-x-auto">
          <table className="text-xs border-collapse">
            <thead>
              <tr>
                <th className="p-2" />
                {columns.map((col) => (
                  <th key={col} className="p-2 text-slate-500 font-medium whitespace-nowrap">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {columns.map((rowCol) => (
                <tr key={rowCol}>
                  <th className="p-2 text-slate-500 font-medium text-left whitespace-nowrap">{rowCol}</th>
                  {columns.map((colCol) => {
                    const value = data[rowCol]?.[colCol] ?? 0;
                    return (
                      <td
                        key={colCol}
                        className="p-2 text-center text-slate-800 border border-slate-200"
                        style={{ backgroundColor: correlationColor(value) }}
                      >
                        {value.toFixed(2)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
