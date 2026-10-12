import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { endpoints } from "@/lib/api";
import { toast } from "sonner";
import { Headset, ShieldCheck, ArrowRight } from "lucide-react";

export default function Onboarding({ onDone }) {
  const { login } = useAuth();
  const [form, setForm] = useState({ id: "ADMIN", name: "" });
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!form.id.trim() || !form.name.trim()) return toast.error("Renseigne un ID et un nom");
    setLoading(true);
    try {
      const r = await endpoints.setup(form);
      toast.success(`Compte administrateur créé : ${r.data.user.name}`);
      login(r.data.user);
      onDone?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Création impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#0f172a] p-6 relative overflow-hidden">
      <div className="absolute inset-0 opacity-25" style={{ backgroundImage: "radial-gradient(circle at 25% 20%, #2563eb 0, transparent 40%), radial-gradient(circle at 75% 70%, #1d4ed8 0, transparent 45%)" }} />
      <div className="relative z-10 w-full max-w-md animate-fade-up">
        <div className="flex items-center gap-3 mb-8 text-white">
          <div className="h-11 w-11 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg">
            <Headset className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="font-display font-extrabold text-lg leading-tight">Support IT</div>
            <div className="text-xs text-blue-200 tracking-wider uppercase">Helpdesk & Stock</div>
          </div>
        </div>

        <div className="rounded-2xl bg-white shadow-2xl p-7">
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="h-5 w-5 text-blue-600" />
            <span className="text-xs uppercase tracking-wider font-bold text-blue-600">Première configuration</span>
          </div>
          <h1 className="font-display text-2xl font-bold text-slate-900">Crée ton compte administrateur</h1>
          <p className="mt-1.5 text-sm text-slate-500">C'est la première fois que la plateforme démarre. Crée le compte admin principal pour commencer.</p>

          <div className="mt-6 space-y-4">
            <div>
              <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Nom complet</label>
              <input data-testid="onboarding-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ales" className="mt-1.5 w-full h-11 rounded-lg border border-slate-200 px-4 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">ID de connexion</label>
              <input data-testid="onboarding-id-input" value={form.id} onChange={(e) => setForm({ ...form, id: e.target.value })} placeholder="ADMIN" className="mt-1.5 w-full h-11 rounded-lg border border-slate-200 px-4 text-sm font-mono uppercase focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none" />
              <p className="mt-1 text-xs text-slate-400">Tu utiliseras cet ID pour te connecter (pas de mot de passe).</p>
            </div>
            <button data-testid="onboarding-submit" onClick={submit} disabled={loading} className="w-full h-11 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors flex items-center justify-center gap-2 disabled:opacity-60">
              Démarrer <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
