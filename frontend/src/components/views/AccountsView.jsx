import { useState, useEffect, useCallback } from "react";
import { endpoints } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { UsersRound, UserPlus, Trash2, ShieldCheck, User } from "lucide-react";

export const AccountsView = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ id: "", name: "", role: "employee", title: "", can_access_parc: false });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const r = await endpoints.users();
    setUsers(r.data);
  }, []);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    if (!form.id.trim() || !form.name.trim()) return toast.error("ID et nom obligatoires");
    setSaving(true);
    try {
      await endpoints.createUser(form);
      toast.success(`Compte ${form.id.toUpperCase()} créé`);
      setForm({ id: "", name: "", role: "employee", title: "", can_access_parc: false });
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de la création");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (u) => {
    try {
      await endpoints.deleteUser(u.id);
      toast.success(`Compte ${u.id} supprimé`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Suppression impossible");
    }
  };

  const admins = users.filter((u) => u.role === "admin");
  const employees = users.filter((u) => u.role === "employee");

  return (
    <div className="animate-fade-up">
      <div className="mb-5">
        <h2 className="font-display text-2xl font-bold text-slate-900">Comptes & accès</h2>
        <p className="text-sm text-slate-500">Crée et gère les identifiants de connexion de l'équipe</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create form */}
        <div className="lg:col-span-1">
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-5 sticky top-4">
            <div className="flex items-center gap-2 mb-4">
              <div className="h-9 w-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center"><UserPlus className="h-[18px] w-[18px]" /></div>
              <h3 className="font-semibold text-slate-800">Nouveau compte</h3>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">ID de connexion</label>
                <input data-testid="account-id-input" value={form.id} onChange={(e) => setForm({ ...form, id: e.target.value })} placeholder="EMP-004" className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm font-mono uppercase focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Nom complet</label>
                <input data-testid="account-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Jean Dupont" className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Rôle</label>
                <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                  <SelectTrigger data-testid="account-role-select" className="mt-1.5 bg-white"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-white border border-slate-200 shadow-lg z-50">
                    <SelectItem value="employee" data-testid="account-role-employee">Employé (crée ses tickets)</SelectItem>
                    <SelectItem value="admin" data-testid="account-role-admin">Admin IT (accès complet)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Poste (optionnel)</label>
                <input data-testid="account-title-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Responsable Ventes" className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              {form.role === "employee" ? (
                <label data-testid="account-parc-toggle" className="flex items-center gap-2.5 rounded-lg border border-slate-200 p-3 cursor-pointer hover:bg-slate-50 transition-colors">
                  <input type="checkbox" data-testid="account-parc-checkbox" checked={form.can_access_parc} onChange={(e) => setForm({ ...form, can_access_parc: e.target.checked })} className="h-4 w-4 accent-blue-600" />
                  <span className="text-sm text-slate-700">Accès au parc informatique</span>
                </label>
              ) : (
                <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 text-xs text-blue-700">Les admins ont accès à tout, y compris le parc informatique.</div>
              )}
              <button data-testid="account-create-button" onClick={create} disabled={saving} className="w-full h-10 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors flex items-center justify-center gap-2 disabled:opacity-60">
                <UserPlus className="h-4 w-4" /> Créer le compte
              </button>
            </div>
          </div>
        </div>

        {/* Lists */}
        <div className="lg:col-span-2 space-y-6">
          <AccountGroup title="Admins IT" icon={ShieldCheck} tone="blue" list={admins} currentId={user.id} onDelete={remove} />
          <AccountGroup title="Employés" icon={User} tone="slate" list={employees} currentId={user.id} onDelete={remove} />
        </div>
      </div>
    </div>
  );
};

const AccountGroup = ({ title, icon: Icon, tone, list, currentId, onDelete }) => (
  <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
    <div className="flex items-center gap-2 px-5 py-3.5 border-b border-slate-100">
      <Icon className={`h-4 w-4 ${tone === "blue" ? "text-blue-600" : "text-slate-500"}`} />
      <h3 className="font-semibold text-slate-800">{title}</h3>
      <span className="ml-auto text-xs font-semibold text-slate-400 tabular-nums">{list.length}</span>
    </div>
    <div className="divide-y divide-slate-100">
      {list.map((u) => (
        <div key={u.id} data-testid={`account-row-${u.id}`} className="flex items-center gap-3 px-5 py-3 hover:bg-slate-50/80 transition-colors">
          <div className={`h-9 w-9 rounded-full flex items-center justify-center text-white text-xs font-bold ${u.role === "admin" ? "bg-blue-600" : "bg-slate-400"}`}>
            {u.name.split(" ").map((p) => p[0]).join("").slice(0, 2)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-slate-800 truncate">{u.name}{u.id === currentId && <span className="ml-2 text-[10px] uppercase tracking-wide font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">Vous</span>}</div>
            <div className="text-xs text-slate-500 truncate">{u.title || "—"}</div>
          </div>
          <span className="font-mono text-xs text-slate-400">{u.id}</span>
          {u.role === "employee" && u.can_access_parc && (
            <span className="text-[10px] uppercase tracking-wide font-bold text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded">Parc</span>
          )}
          <button data-testid={`account-delete-${u.id}`} onClick={() => onDelete(u)} disabled={u.id === currentId} className="h-8 w-8 rounded-md flex items-center justify-center text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors disabled:opacity-30 disabled:cursor-not-allowed" title={u.id === currentId ? "Vous ne pouvez pas supprimer votre propre compte" : "Supprimer"}>
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
      {list.length === 0 && <div className="px-5 py-8 text-center text-sm text-slate-400">Aucun compte</div>}
    </div>
  </div>
);
