import { useEffect, useState } from "react";
import { Ship, LogOut } from "lucide-react";

// Top header bar: vessel name, a live clock, a pulsing "Live" badge, and logout.
export default function Header({ onLogout }) {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const intervalId = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-sky-50 border border-sky-200">
          <Ship size={20} className="text-sky-600" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-800 tracking-wide">IKRAAM SEA LINE</h1>
          <p className="text-xs text-slate-400">Marine Machinery Fault Detection Dashboard</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-500 font-mono">
          {now.toLocaleDateString()} &nbsp; {now.toLocaleTimeString()}
        </span>
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-600 text-xs font-semibold">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          LIVE
        </span>
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-500 border border-slate-200 hover:bg-slate-50 hover:text-slate-700 transition-colors"
        >
          <LogOut size={14} />
          Logout
        </button>
      </div>
    </header>
  );
}
