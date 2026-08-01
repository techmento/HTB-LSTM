import { Cpu, Database, Hash, Clock } from "lucide-react";

export default function Footer({ totalRecords, lastUpdated }) {
  return (
    <footer className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 border-t border-slate-200 bg-white text-xs text-slate-400">
      <div className="flex items-center gap-1.5">
        <Cpu size={14} />
        Model: <span className="text-slate-600">Hybrid Random Forest-LSTM</span>
      </div>
      <div className="flex items-center gap-1.5">
        <Database size={14} />
        Dataset: <span className="text-slate-600">Ikraam Sea Line Operational Data</span>
      </div>
      <div className="flex items-center gap-1.5">
        <Hash size={14} />
        Total Records: <span className="text-slate-600">{totalRecords ?? "—"}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <Clock size={14} />
        Last Updated: <span className="text-slate-600">{lastUpdated ? lastUpdated.toLocaleString() : "—"}</span>
      </div>
    </footer>
  );
}
