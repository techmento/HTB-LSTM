import { Database, CheckCircle2, AlertTriangle, XCircle, ShieldCheck, ShieldAlert } from "lucide-react";
import Card from "./Card";
import { getSeverity } from "../utils/severity";
import { getLatestPerMachine } from "../utils/machines";

// Overall system is flagged UNSTABLE once more than 15% of machines are in
// the "fault" severity tier (based on each machine's most recent reading).
// This threshold is a simple, defensible choice for a small project — not
// derived from the data itself.
const UNSTABLE_THRESHOLD_PERCENT = 15;

export default function SummaryCards({ results }) {
  // Counts are per-machine (current status), matching the Fault Probability
  // chart — not per-row, so a machine with 10 readings doesn't get counted
  // 10 times just because it was uploaded 10 times.
  const latestPerMachine = getLatestPerMachine(results);
  const total = latestPerMachine.length;

  let healthy = 0;
  let warning = 0;
  let fault = 0;
  for (const row of latestPerMachine) {
    const severity = getSeverity(row.fault_probability);
    if (severity === "healthy") healthy += 1;
    else if (severity === "warning") warning += 1;
    else fault += 1;
  }

  const pct = (count) => (total ? ((count / total) * 100).toFixed(1) : "0.0");
  const faultPercentage = total ? (fault / total) * 100 : 0;
  const isStable = faultPercentage <= UNSTABLE_THRESHOLD_PERCENT;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <Card>
        <StatBlock icon={Database} iconColor="text-sky-600" label="Total Machines" value={total} />
      </Card>
      <Card>
        <StatBlock
          icon={CheckCircle2}
          iconColor="text-emerald-600"
          label="Healthy"
          value={healthy}
          sub={`${pct(healthy)}%`}
        />
      </Card>
      <Card>
        <StatBlock
          icon={AlertTriangle}
          iconColor="text-amber-600"
          label="Warning"
          value={warning}
          sub={`${pct(warning)}%`}
        />
      </Card>
      <Card>
        <StatBlock icon={XCircle} iconColor="text-red-600" label="Fault" value={fault} sub={`${pct(fault)}%`} />
      </Card>
      <Card>
        <StatBlock
          icon={isStable ? ShieldCheck : ShieldAlert}
          iconColor={isStable ? "text-emerald-600" : "text-red-600"}
          label="System Status"
          value={total === 0 ? "—" : isStable ? "STABLE" : "UNSTABLE"}
          valueClassName={total === 0 ? "text-slate-400" : isStable ? "text-emerald-600" : "text-red-600"}
        />
      </Card>
    </div>
  );
}

function StatBlock({ icon: Icon, iconColor, label, value, sub, valueClassName = "text-slate-800" }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Icon size={16} className={iconColor} />
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl font-bold ${valueClassName}`}>{value}</span>
        {sub && <span className="text-xs text-slate-400">{sub}</span>}
      </div>
    </div>
  );
}
