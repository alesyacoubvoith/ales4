import { useState, useEffect, useCallback } from "react";
import { endpoints } from "@/lib/api";
import { StatCard, StatusBadge, PriorityBadge } from "@/components/Bits";
import { formatDateTime, daysUntil, formatDate } from "@/lib/ui";
import { Ticket, AlertTriangle, CheckCircle2, LogIn, ArrowRight, BellRing } from "lucide-react";

export const OverviewView = ({ setActive }) => {
  const [stats, setStats] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [reminders, setReminders] = useState([]);

  const load = useCallback(async () => {
    const [s, t, r] = await Promise.all([endpoints.stats(), endpoints.tickets({}), endpoints.reminders()]);
    setStats(s.data);
    setTickets(t.data.slice(0, 6));
    setReminders(r.data.filter((x) => !x.done).slice(0, 4));
  }, []);

  useEffect(() => { load(); }, [load]);

  if (!stats) return <div className="text-slate-400">Chargement...</div>;

  const maxStatus = Math.max(...Object.values(stats.by_status), 1);

  return (
    <div className="animate-fade-up space-y-6">
      <div>
        <h2 className="font-display text-2xl font-bold text-slate-900">Tableau de bord</h2>
        <p className="text-sm text-slate-500">Vue d'ensemble de l'activité support & stock</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Tickets ouverts" value={stats.open_tickets} icon={Ticket} tone="blue" hint={`${stats.total_tickets} au total`} />
        <StatCard label="Stock en alerte" value={stats.low_stock} icon={AlertTriangle} tone="amber" hint={`${stats.total_items} articles`} />
        <StatCard label="Tickets résolus" value={stats.resolved} icon={CheckCircle2} tone="emerald" />
        <StatCard label="Connexions aujourd'hui" value={stats.logs_today} icon={LogIn} tone="slate" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-800">Tickets récents</h3>
            <button data-testid="go-tickets" onClick={() => setActive("tickets")} className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1">Voir tout <ArrowRight className="h-3 w-3" /></button>
          </div>
          <div className="divide-y divide-slate-100">
            {tickets.map((t) => (
              <div key={t.id} className="px-5 py-3 flex items-center gap-3 hover:bg-slate-50/80 transition-colors">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-slate-800 truncate">{t.title}</div>
                  <div className="text-xs text-slate-400">{t.creator_name} · {formatDateTime(t.created_at)}</div>
                </div>
                <PriorityBadge priority={t.priority} />
                <StatusBadge status={t.status} />
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-5">
            <h3 className="font-semibold text-slate-800 mb-4">Répartition par statut</h3>
            <div className="space-y-3">
              {Object.entries(stats.by_status).map(([s, n]) => (
                <div key={s}>
                  <div className="flex justify-between text-xs mb-1"><span className="text-slate-600">{s}</span><span className="font-semibold text-slate-800 tabular-nums">{n}</span></div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden"><div className="h-full rounded-full bg-blue-500 transition-all" style={{ width: `${(n / maxStatus) * 100}%` }} /></div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">Prochains rappels</h3>
              <button data-testid="go-reminders" onClick={() => setActive("reminders")} className="text-xs font-semibold text-blue-600 hover:text-blue-700">Voir</button>
            </div>
            <div className="space-y-2.5">
              {reminders.map((r) => {
                const days = daysUntil(r.due_date);
                return (
                  <div key={r.id} className="flex items-center gap-2.5">
                    <BellRing className={`h-4 w-4 shrink-0 ${days <= 7 ? "text-amber-500" : "text-slate-400"}`} />
                    <div className="flex-1 min-w-0"><div className="text-sm text-slate-700 truncate">{r.title}</div><div className="text-[11px] text-slate-400">{formatDate(r.due_date)}</div></div>
                    <span className={`text-[11px] font-semibold ${days <= 7 ? "text-amber-600" : "text-slate-400"}`}>{days}j</span>
                  </div>
                );
              })}
              {reminders.length === 0 && <div className="text-sm text-slate-400">Aucun rappel à venir</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
