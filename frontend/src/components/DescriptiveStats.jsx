import { Table2 } from "lucide-react";
import Card from "./Card";
import StatusState from "./StatusState";

function fmt(value) {
  return typeof value === "number" ? value.toFixed(2) : "—";
}

// descriptive_stats comes from pandas df.describe(), which includes count
// and percentiles too — we only surface mean/std/min/max here since that's
// what the dashboard card is meant to show.
export default function DescriptiveStats({ data, loading, error }) {
  return (
    <Card title="Descriptive Statistics" icon={Table2}>
      <StatusState loading={loading} error={error} />
      {!loading && !error && data && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase tracking-wide border-b border-slate-200">
                <th className="py-2 pr-4">Variable</th>
                <th className="py-2 pr-4">Mean</th>
                <th className="py-2 pr-4">Std Dev</th>
                <th className="py-2 pr-4">Min</th>
                <th className="py-2 pr-4">Max</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data).map(([column, stats]) => (
                <tr key={column} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 pr-4 text-slate-700">{column}</td>
                  <td className="py-2 pr-4 text-slate-500">{fmt(stats.mean)}</td>
                  <td className="py-2 pr-4 text-slate-500">{fmt(stats.std)}</td>
                  <td className="py-2 pr-4 text-slate-500">{fmt(stats.min)}</td>
                  <td className="py-2 pr-4 text-slate-500">{fmt(stats.max)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
