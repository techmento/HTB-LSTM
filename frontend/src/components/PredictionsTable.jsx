import { ListChecks } from "lucide-react";
import Card from "./Card";
import { getSeverity, SEVERITY_STYLES } from "../utils/severity";
import { getLatestPerMachine } from "../utils/machines";

export default function PredictionsTable({ results }) {
  // One row per machine (its most recent reading), matching Summary Cards
  // and the Fault Probability chart — not every row in the upload.
  const latestPerMachine = getLatestPerMachine(results);

  return (
    <Card title="Latest Predictions" icon={ListChecks}>
      {latestPerMachine.length === 0 ? (
        <div className="py-10 text-center text-sm text-slate-400">
          No predictions yet — upload a file or submit a manual reading above.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase tracking-wide border-b border-slate-200">
                <th className="py-2 pr-4">Machine</th>
                <th className="py-2 pr-4">Prediction</th>
                <th className="py-2 pr-4">Probability</th>
                <th className="py-2 pr-4">Fault Types</th>
              </tr>
            </thead>
            <tbody>
              {latestPerMachine.map((row) => {
                const severity = getSeverity(row.fault_probability);
                const style = SEVERITY_STYLES[severity];
                return (
                  <tr key={row.row_index} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 text-slate-700">{row.machine_id}</td>
                    <td className="py-2 pr-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text} border ${style.border}`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-slate-500">{(row.fault_probability * 100).toFixed(1)}%</td>
                    <td className="py-2 pr-4 text-slate-500">{row.fault_types.join(", ")}</td>
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
