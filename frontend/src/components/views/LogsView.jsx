import { useState, useEffect } from "react";
import { endpoints } from "@/lib/api";
import { formatDateTime } from "@/lib/ui";
import { ScrollText, Monitor, Smartphone } from "lucide-react";

export const LogsView = () => {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    endpoints.logs().then((r) => setLogs(r.data)).catch(() => {});
  }, []);

  return (
    <div className="animate-fade-up">
      <div className="mb-5">
        <h2 className="font-display text-2xl font-bold text-slate-900">Logs de connexion</h2>
        <p className="text-sm text-slate-500">{logs.length} connexion(s) enregistrée(s)</p>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-600 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold py-3.5 px-4">Employé</th>
                <th className="text-left font-semibold py-3.5 px-4 hidden sm:table-cell">ID</th>
                <th className="text-left font-semibold py-3.5 px-4">Date & heure</th>
                <th className="text-left font-semibold py-3.5 px-4 hidden md:table-cell">Appareil</th>
                <th className="text-left font-semibold py-3.5 px-4 hidden lg:table-cell">IP</th>
                <th className="text-left font-semibold py-3.5 px-4">Statut</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((l) => (
                <tr key={l.id} data-testid={`log-row-${l.id}`} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2.5">
                      <div className={`h-8 w-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold ${l.role === "admin" ? "bg-blue-600" : "bg-slate-400"}`}>
                        {l.employee_name.split(" ").map((p) => p[0]).join("").slice(0, 2)}
                      </div>
                      <div>
                        <div className="font-medium text-slate-800">{l.employee_name}</div>
                        <div className="text-[11px] text-slate-400">{l.role === "admin" ? "Admin" : "Employé"}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 hidden sm:table-cell font-mono text-xs text-slate-500">{l.employee_id}</td>
                  <td className="py-3 px-4 text-slate-600">{formatDateTime(l.login_time)}</td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    <span className="inline-flex items-center gap-1.5 text-slate-600">
                      {l.device_type === "Mobile" ? <Smartphone className="h-3.5 w-3.5" /> : <Monitor className="h-3.5 w-3.5" />}
                      {l.device_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell font-mono text-xs text-slate-500">{l.ip_address}</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 text-emerald-700 px-2.5 py-0.5 text-xs font-medium">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />{l.status}
                    </span>
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={6} className="py-16 text-center text-slate-400">
                  <ScrollText className="h-8 w-8 mx-auto mb-2 text-slate-300" />Aucune connexion
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
