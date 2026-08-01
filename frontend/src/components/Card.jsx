// Small reusable panel used by almost every section of the dashboard, so
// each one doesn't have to repeat the same background/border/heading markup.
export default function Card({ title, icon: Icon, children, className = "", right = null }) {
  return (
    <div className={`bg-white border border-slate-200 rounded-xl shadow-sm p-4 ${className}`}>
      {title && (
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {Icon && <Icon size={16} className="text-slate-400" />}
            <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
              {title}
            </h3>
          </div>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}
