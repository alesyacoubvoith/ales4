import { statusStyles, statusDot, priorityStyles } from "@/lib/ui";

export const StatusBadge = ({ status }) => (
  <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusStyles[status] || "bg-slate-100 text-slate-600 border-slate-200"}`}>
    <span className={`h-1.5 w-1.5 rounded-full ${statusDot[status] || "bg-slate-400"}`} />
    {status}
  </span>
);

export const PriorityBadge = ({ priority }) => (
  <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${priorityStyles[priority] || "bg-slate-100 text-slate-600 border-slate-200"}`}>
    {priority}
  </span>
);

export const StatCard = ({ label, value, icon: Icon, tone = "blue", hint }) => {
  const tones = {
    blue: "bg-blue-50 text-blue-600",
    amber: "bg-amber-50 text-amber-600",
    emerald: "bg-emerald-50 text-emerald-600",
    slate: "bg-slate-100 text-slate-600",
  };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-blue-300 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider font-semibold text-slate-500">{label}</span>
        <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${tones[tone]}`}>
          <Icon className="h-[18px] w-[18px]" />
        </div>
      </div>
      <div className="mt-3 text-3xl font-display font-extrabold text-slate-900 tabular-nums">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}
    </div>
  );
};
