import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { endpoints } from "@/lib/api";
import { toast } from "sonner";
import { ShieldCheck, LogIn, Headset, User, Boxes, Ticket } from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const [users, setUsers] = useState([]);
  const [id, setId] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    endpoints.users().then((r) => setUsers(r.data)).catch(() => {});
  }, []);

  const doLogin = async (employeeId) => {
    if (!employeeId) return toast.error("Entre ton ID employé");
    setLoading(true);
    try {
      const r = await endpoints.login(employeeId);
      login(r.data.user);
      toast.success(`Bienvenue ${r.data.user.name}`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Connexion impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row">
      {/* Left brand panel */}
      <div className="relative hidden lg:flex lg:w-1/2 flex-col justify-between p-12 bg-[#0f172a] overflow-hidden">
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: "radial-gradient(circle at 20% 20%, #2563eb 0, transparent 40%), radial-gradient(circle at 80% 60%, #1d4ed8 0, transparent 45%)" }} />
        <div className="relative z-10 flex items-center gap-3 text-white">
          <div className="h-11 w-11 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg">
            <Headset className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="font-display font-extrabold text-lg leading-tight">Support IT</div>
            <div className="text-xs text-blue-200 tracking-wider uppercase">IT Helpdesk & Stock</div>
          </div>
        </div>
        <div className="relative z-10 text-white max-w-md">
          <h1 className="font-display text-4xl font-extrabold leading-tight tracking-tight">La plateforme support de ton équipe IT.</h1>
          <p className="mt-4 text-slate-300 leading-relaxed">Chaque collaborateur lance un ticket, l'équipe support suit tout, et le stock reste sous contrôle.</p>
          <div className="mt-8 grid grid-cols-3 gap-4">
            {[["Tickets", Ticket], ["Stock", Boxes], ["Logs", ShieldCheck]].map(([label, Icon]) => (
              <div key={label} className="rounded-xl bg-white/5 border border-white/10 p-4 backdrop-blur-sm">
                <Icon className="h-5 w-5 text-blue-300" />
                <div className="mt-2 text-sm font-medium text-white">{label}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="relative z-10 text-xs text-slate-400">Connexion par ID employé — sans mot de passe.</div>
      </div>

      {/* Right login form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 bg-slate-50">
        <div className="w-full max-w-md animate-fade-up">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center">
              <Headset className="h-5 w-5 text-white" />
            </div>
            <div className="font-display font-extrabold text-lg">Support IT · Helpdesk</div>
          </div>
          <h2 className="font-display text-2xl font-bold text-slate-900">Connexion</h2>
          <p className="mt-1 text-sm text-slate-500">Saisis ton identifiant employé pour accéder à la plateforme.</p>

          <div className="mt-6">
            <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">ID Employé</label>
            <div className="mt-2 flex gap-2">
              <input
                data-testid="login-id-input"
                value={id}
                onChange={(e) => setId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && doLogin(id)}
                placeholder="EMP-001"
                className="flex-1 h-11 rounded-lg border border-slate-200 bg-white px-4 text-sm font-mono uppercase text-slate-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none"
              />
              <button
                data-testid="login-submit-button"
                onClick={() => doLogin(id)}
                disabled={loading}
                className="h-11 px-5 rounded-lg bg-blue-600 text-white text-sm font-semibold flex items-center gap-2 hover:bg-blue-700 active:scale-[0.98] transition-colors disabled:opacity-60"
              >
                <LogIn className="h-4 w-4" /> Entrer
              </button>
            </div>
          </div>

          <div className="mt-8">
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-3">Accès rapide</div>
            <div className="space-y-2">
              {users.map((u) => (
                <button
                  key={u.id}
                  data-testid={`login-quick-${u.id}`}
                  onClick={() => doLogin(u.id)}
                  className="w-full flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 text-left hover:border-blue-300 hover:bg-blue-50/50 transition-colors group"
                >
                  <div className={`h-9 w-9 rounded-full flex items-center justify-center text-white text-xs font-bold ${u.role === "admin" ? "bg-blue-600" : "bg-slate-400"}`}>
                    {u.name.split(" ").map((p) => p[0]).join("").slice(0, 2)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-slate-800 truncate">{u.name}</div>
                    <div className="text-xs text-slate-500 truncate">{u.title}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {u.role === "admin" && <span className="text-[10px] uppercase tracking-wide font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">Admin</span>}
                    <span className="text-xs font-mono text-slate-400">{u.id}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
