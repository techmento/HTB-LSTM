import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { HeartPulse } from "lucide-react";
import Card from "./Card";
import StatusState from "./StatusState";

const COLORS = { Normal: "#10b981", Fault: "#ef4444" };

export default function FaultDistribution({ data, loading, error }) {
  const chartData = data
    ? Object.entries(data).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <Card title="Fault Health Distribution" icon={HeartPulse}>
      <StatusState loading={loading} error={error} />
      {!loading && !error && data && (
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={2}
              label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name] || "#64748b"} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: 12, color: "#64748b" }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
