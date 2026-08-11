import { Award } from "lucide-react";
import Card from "./Card";
import StatusState from "./StatusState";

const MODEL_LABELS = {
  random_forest: "Random Forest",
  lstm: "LSTM",
  hybrid: "Hybrid",
};

const METRICS = [
  { key: "accuracy", label: "Accuracy" },
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1_score", label: "F1-Score" },
];

export default function ModelPerformance({ data, loading, error }) {
  const modelKeys = data ? Object.keys(data) : [];

  return (
    <Card title="Hybrid Model Performance" icon={Award}>
      <StatusState loading={loading} error={error} />
      {!loading && !error && data && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase tracking-wide border-b border-slate-200">
                <th className="py-2 pr-4">Metric</th>
                {modelKeys.map((key) => (
                  <th key={key} className="py-2 pr-4">{MODEL_LABELS[key] || key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {METRICS.map(({ key, label }) => {
                const best = Math.max(...modelKeys.map((m) => data[m][key]));
                return (
                  <tr key={key} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 text-slate-700">{label}</td>
                    {modelKeys.map((m) => {
                      const value = data[m][key];
                      const isBest = value === best;
                      return (
                        <td
                          key={m}
                          className={`py-2 pr-4 ${isBest ? "text-emerald-600 font-semibold" : "text-slate-500"}`}
                        >
                          {(value * 100).toFixed(2)}%
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
