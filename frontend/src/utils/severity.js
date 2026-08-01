// Shared thresholds for turning a fault_probability (0-1) into a 3-tier
// severity used for colors across the dashboard: healthy (green),
// warning (amber), fault (red). Defined once here so every component uses
// the exact same cutoffs instead of re-declaring "0.3" / "0.5" everywhere.
export function getSeverity(faultProbability) {
  if (faultProbability >= 0.5) return "fault";
  if (faultProbability >= 0.3) return "warning";
  return "healthy";
}

export const SEVERITY_STYLES = {
  healthy: {
    text: "text-emerald-600",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    hex: "#10b981",
    label: "Healthy",
  },
  warning: {
    text: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-200",
    hex: "#f59e0b",
    label: "Warning",
  },
  fault: {
    text: "text-red-600",
    bg: "bg-red-50",
    border: "border-red-200",
    hex: "#ef4444",
    label: "Fault",
  },
};
