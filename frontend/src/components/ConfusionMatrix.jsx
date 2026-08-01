import { Grid2x2 } from "lucide-react";
import Card from "./Card";
import StatusState from "./StatusState";

// hybrid.confusion_matrix is [[TN, FP], [FN, TP]] (label 0 = Healthy, 1 = Fault).
export default function ConfusionMatrix({ data, loading, error }) {
  const matrix = data?.hybrid?.confusion_matrix;
  const [[tn, fp], [fn, tp]] = matrix || [[0, 0], [0, 0]];

  return (
    <Card title="Confusion Matrix (Hybrid Model)" icon={Grid2x2}>
      <StatusState loading={loading} error={error} />
      {!loading && !error && matrix && (
        <div className="max-w-sm mx-auto">
          <div className="grid grid-cols-[auto_1fr_1fr] gap-2 text-center text-xs">
            <div />
            <div className="text-slate-500 pb-1">Predicted Healthy</div>
            <div className="text-slate-500 pb-1">Predicted Fault</div>

            <div className="flex items-center justify-center text-slate-500 -rotate-0 pr-1">Actual Healthy</div>
            <Cell value={tn} tone="correct" />
            <Cell value={fp} tone="wrong" />

            <div className="flex items-center justify-center text-slate-500 pr-1">Actual Fault</div>
            <Cell value={fn} tone="wrong" />
            <Cell value={tp} tone="correct" />
          </div>
        </div>
      )}
    </Card>
  );
}

function Cell({ value, tone }) {
  const style =
    tone === "correct"
      ? "bg-emerald-50 border-emerald-200 text-emerald-600"
      : "bg-red-50 border-red-200 text-red-600";
  return (
    <div className={`rounded-lg border ${style} py-4 text-xl font-bold`}>
      {value}
    </div>
  );
}
