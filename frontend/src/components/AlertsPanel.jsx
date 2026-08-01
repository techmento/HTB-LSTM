import { AlertOctagon, ShieldCheck } from "lucide-react";
import Card from "./Card";
import { getLatestPerMachine } from "../utils/machines";

// Only machines whose MOST RECENT reading is "Fault" (the backend's own
// binary status field) show up here — a machine that had a fault earlier
// but has since recovered won't show an active alert anymore.
export default function AlertsPanel({ results }) {
  const latestPerMachine = getLatestPerMachine(results);
  const faults = latestPerMachine.filter((row) => row.status === "Fault");

  return (
    <Card title="Active Alerts" icon={AlertOctagon}>
      {faults.length === 0 ? (
        <div className="py-8 flex flex-col items-center gap-2 text-emerald-600">
          <ShieldCheck size={24} />
          <p className="text-sm">No active faults detected.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {faults.map((row) => (
            <div
              key={row.row_index}
              className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg px-4 py-3"
            >
              <AlertOctagon size={18} className="text-red-500 mt-0.5 shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-800">
                  {row.machine_id} &mdash; {(row.fault_probability * 100).toFixed(1)}% fault probability
                </p>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {row.fault_types.map((type) => (
                    <span
                      key={type}
                      className="text-xs px-2 py-0.5 rounded-full bg-red-100 border border-red-200 text-red-700"
                    >
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
