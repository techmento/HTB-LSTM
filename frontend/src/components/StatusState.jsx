import { Loader2, AlertCircle } from "lucide-react";

// Shared loading/error placeholder for the sections that fetch once on
// mount (dataset stats, model performance) — avoids repeating the same
// spinner/error markup in every one of those components.
export default function StatusState({ loading, error, height = 180 }) {
  if (loading) {
    return (
      <div style={{ height }} className="flex items-center justify-center gap-2 text-sm text-slate-400">
        <Loader2 size={16} className="animate-spin" />
        Loading...
      </div>
    );
  }
  if (error) {
    return (
      <div style={{ height }} className="flex items-center justify-center gap-2 text-sm text-red-500">
        <AlertCircle size={16} />
        {error}
      </div>
    );
  }
  return null;
}
