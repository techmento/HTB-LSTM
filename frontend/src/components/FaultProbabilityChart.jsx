import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Gauge } from "lucide-react";
import Card from "./Card";
import { getSeverity, SEVERITY_STYLES } from "../utils/severity";
import { getLatestPerMachine } from "../utils/machines";

// Bar chart of fault probability (%) — one bar per machine, colored
// green/amber/red by the same severity tiers used everywhere else.
export default function FaultProbabilityChart({ results }) {
  const latestPerMachine = getLatestPerMachine(results);

  const data = latestPerMachine.map((row) => ({
    name: row.machine_id,
    probability: Number((row.fault_probability * 100).toFixed(1)),
    severity: getSeverity(row.fault_probability),
  }));

  return (
    <Card title="Machine Fault Probability" icon={Gauge}>
      {data.length === 0 ? (
        <EmptyState />
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} interval={0} angle={-30} textAnchor="end" height={60} />
            <YAxis stroke="#94a3b8" fontSize={11} unit="%" domain={[0, 100]} />
            <Tooltip
              contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8 }}
              labelStyle={{ color: "#0f172a" }}
              formatter={(value) => [`${value}%`, "Fault Probability"]}
            />
            <Bar dataKey="probability" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={index} fill={SEVERITY_STYLES[entry.severity].hex} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

function EmptyState() {
  return (
    <div className="h-[260px] flex items-center justify-center text-sm text-slate-500">
      No predictions yet — upload a file or submit a manual reading above.
    </div>
  );
}
