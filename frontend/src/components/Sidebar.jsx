import { useState } from "react";
import {
  Ship,
  LayoutDashboard,
  BarChart3,
  Radio,
  Gauge,
  PieChart,
  Award,
  AlertTriangle,
  FileText,
  Settings,
} from "lucide-react";

// Each nav item scrolls to the matching section id on the dashboard (see
// App.jsx). This stays a single page — no router, no URL changes — clicking
// a link just moves the viewport, the same as a page's own table of contents.
// `id` is unique per nav item and drives which one is highlighted.
// `sectionId` is the DOM id it scrolls to — Settings has no section of its
// own, so it reuses Dashboard's, but still gets its own highlight.
const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, sectionId: "section-dashboard" },
  { id: "overview", label: "Overview", icon: BarChart3, sectionId: "section-overview" },
  { id: "live-data", label: "Live Data", icon: Radio, sectionId: "section-live-data" },
  { id: "predictions", label: "Predictions", icon: Gauge, sectionId: "section-predictions" },
  { id: "analytics", label: "Analytics", icon: PieChart, sectionId: "section-analytics" },
  { id: "performance", label: "Performance", icon: Award, sectionId: "section-performance" },
  { id: "alerts", label: "Alerts", icon: AlertTriangle, sectionId: "section-alerts" },
  { id: "reports", label: "Reports", icon: FileText, sectionId: "section-reports" },
  // No dedicated settings panel exists on this dashboard, so it falls back
  // to the top of the page rather than pretending to go somewhere real.
  { id: "settings", label: "Settings", icon: Settings, sectionId: "section-dashboard" },
];

export default function Sidebar() {
  const [activeId, setActiveId] = useState("dashboard");

  function handleNavClick(id, sectionId) {
    setActiveId(id);
    document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <aside className="w-60 shrink-0 bg-white border-r border-slate-200 flex flex-col">
      {/* Brand block — matches the header's height/padding on the right so
          the two line up, instead of nav links starting flush at the top. */}
      <div className="flex items-center gap-2.5 px-6 py-4 border-b border-slate-200">
        <div className="p-2 rounded-lg bg-sky-50 border border-sky-200">
          <Ship size={18} className="text-sky-600" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-bold text-slate-800">IKRAAM</p>
          <p className="text-[11px] text-slate-400">Fleet Control</p>
        </div>
      </div>

      <nav className="flex flex-col gap-1 px-3 py-4">
        {NAV_ITEMS.map(({ id, label, icon: Icon, sectionId }) => {
          const isActive = activeId === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => handleNavClick(id, sectionId)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-sky-50 border border-sky-200 text-sky-700 font-medium"
                  : "border border-transparent text-slate-500 hover:bg-slate-50 hover:text-slate-700"
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
