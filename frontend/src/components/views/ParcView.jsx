import { useState, useEffect, useCallback, useRef } from "react";
import { api, endpoints } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { MonitorSmartphone, Monitor, Printer, Tablet, Download, Upload, Plus, Pencil, Trash2, Cpu } from "lucide-react";

const TYPE_ICON = { Ordinateur: Monitor, Imprimante: Printer, Tablette: Tablet };
const STATUS_STYLES = {
  "En service": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "En stock": "bg-blue-50 text-blue-700 border-blue-200",
  "En panne": "bg-rose-50 text-rose-700 border-rose-200",
  "Réformé": "bg-slate-100 text-slate-600 border-slate-200",
};
const emptyForm = { name: "", type: "Ordinateur", brand: "", model: "", serial: "", assigned_to: "", status: "En service", purchase_date: "", notes: "" };

export const ParcView = () => {
  const { isAdmin } = useAuth();
  const [assets, setAssets] = useState([]);
  const [meta, setMeta] = useState({ asset_types: [], asset_statuses: [] });
  const [tab, setTab] = useState("Tous");
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    const r = await endpoints.assets();
    setAssets(r.data);
  }, []);

  useEffect(() => {
    load();
    endpoints.meta().then((r) => setMeta(r.data)).catch(() => {});
  }, [load]);

  const tabs = ["Tous", "Ordinateur", "Imprimante", "Tablette"];
  const shown = tab === "Tous" ? assets : assets.filter((a) => a.type === tab);
  const countBy = (t) => assets.filter((a) => a.type === t).length;

  const openAdd = () => { setForm(emptyForm); setModal({ mode: "add" }); };
  const openEdit = (a) => { setForm({ ...a, purchase_date: a.purchase_date || "", brand: a.brand || "", model: a.model || "", serial: a.serial || "", assigned_to: a.assigned_to || "", notes: a.notes || "" }); setModal({ mode: "edit", item: a }); };

  const save = async () => {
    if (!form.name.trim()) return toast.error("Le nom est obligatoire");
    const payload = { ...form, purchase_date: form.purchase_date || null };
    try {
      if (modal.mode === "add") { await endpoints.createAsset(payload); toast.success("Matériel ajouté"); }
      else { await endpoints.updateAsset(modal.item.id, payload); toast.success("Matériel modifié"); }
      setModal(null); load();
    } catch { toast.error("Erreur"); }
  };

  const remove = async (a) => { await endpoints.deleteAsset(a.id); toast.success("Matériel supprimé"); load(); };

  const exportExcel = async () => {
    setExporting(true);
    try {
      const res = await endpoints.exportAssets();
      const url = URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = "parc-informatique.xlsx";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast.success("Export Excel téléchargé");
    } catch {
      toast.error("Export impossible");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="animate-fade-up">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="font-display text-2xl font-bold text-slate-900">Parc informatique</h2>
          <p className="text-sm text-slate-500">{assets.length} matériels · ordinateurs, imprimantes, tablettes</p>
        </div>
        <div className="flex gap-2">
          <button data-testid="export-parc-button" onClick={exportExcel} disabled={exporting} className="h-10 px-4 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 text-sm font-semibold hover:bg-emerald-100 active:scale-[0.98] transition-colors flex items-center gap-2 disabled:opacity-60">
            <Download className="h-4 w-4" /> Exporter Excel
          </button>
          {isAdmin && (
            <button data-testid="add-asset-button" onClick={openAdd} className="h-10 px-4 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors flex items-center gap-2">
              <Plus className="h-4 w-4" /> Ajouter
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-1.5 mb-4 overflow-x-auto">
        {tabs.map((t) => {
          const Icon = TYPE_ICON[t] || Cpu;
          const active = tab === t;
          return (
            <button key={t} data-testid={`parc-tab-${t}`} onClick={() => setTab(t)} className={`h-9 px-3.5 rounded-lg text-sm font-medium whitespace-nowrap flex items-center gap-2 border transition-colors ${active ? "bg-blue-600 text-white border-blue-600" : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"}`}>
              {t !== "Tous" && <Icon className="h-4 w-4" />}
              {t === "Tous" ? "Tous" : t}
              <span className={`text-xs tabular-nums ${active ? "text-blue-100" : "text-slate-400"}`}>{t === "Tous" ? assets.length : countBy(t)}</span>
            </button>
          );
        })}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-600 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold py-3.5 px-4">Matériel</th>
                <th className="text-left font-semibold py-3.5 px-4 hidden md:table-cell">Marque / Modèle</th>
                <th className="text-left font-semibold py-3.5 px-4 hidden lg:table-cell">N° série</th>
                <th className="text-left font-semibold py-3.5 px-4">Affecté à</th>
                <th className="text-left font-semibold py-3.5 px-4">Statut</th>
                {isAdmin && <th className="text-right font-semibold py-3.5 px-4">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {shown.map((a) => {
                const Icon = TYPE_ICON[a.type] || Cpu;
                return (
                  <tr key={a.id} data-testid={`asset-row-${a.id}`} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="h-8 w-8 rounded-lg bg-slate-100 text-slate-500 flex items-center justify-center"><Icon className="h-4 w-4" /></div>
                        <div>
                          <div className="font-medium text-slate-800">{a.name}</div>
                          <div className="text-xs text-slate-400">{a.type}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 hidden md:table-cell text-slate-600">{[a.brand, a.model].filter(Boolean).join(" ") || "—"}</td>
                    <td className="py-3 px-4 hidden lg:table-cell font-mono text-xs text-slate-500">{a.serial || "—"}</td>
                    <td className="py-3 px-4 text-slate-600">{a.assigned_to || "—"}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[a.status] || "bg-slate-100 text-slate-600 border-slate-200"}`}>{a.status}</span>
                    </td>
                    {isAdmin && (
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          <button data-testid={`edit-asset-${a.id}`} onClick={() => openEdit(a)} className="h-8 w-8 rounded-md flex items-center justify-center text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"><Pencil className="h-4 w-4" /></button>
                          <button data-testid={`delete-asset-${a.id}`} onClick={() => remove(a)} className="h-8 w-8 rounded-md flex items-center justify-center text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"><Trash2 className="h-4 w-4" /></button>
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })}
              {shown.length === 0 && (
                <tr><td colSpan={isAdmin ? 6 : 5} className="py-16 text-center text-slate-400">
                  <MonitorSmartphone className="h-8 w-8 mx-auto mb-2 text-slate-300" />Aucun matériel
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Dialog open={!!modal} onOpenChange={(o) => !o && setModal(null)}>
        <DialogContent className="bg-white sm:max-w-lg" data-testid="asset-modal">
          <DialogHeader><DialogTitle className="font-display text-xl">{modal?.mode === "add" ? "Ajouter un matériel" : "Modifier le matériel"}</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-1 max-h-[65vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Nom / Réf</label>
                <input data-testid="asset-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="PC-BUREAU-204" className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Type</label>
                <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                  <SelectTrigger data-testid="asset-type-select" className="mt-1.5 bg-white"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-white border border-slate-200 shadow-lg z-50">
                    {meta.asset_types.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Marque</label>
                <input data-testid="asset-brand-input" value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} placeholder="Dell" className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Modèle</label>
                <input data-testid="asset-model-input" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} placeholder="OptiPlex 7090" className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">N° série</label>
                <input data-testid="asset-serial-input" value={form.serial} onChange={(e) => setForm({ ...form, serial: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Affecté à</label>
                <input data-testid="asset-assigned-input" value={form.assigned_to} onChange={(e) => setForm({ ...form, assigned_to: e.target.value })} placeholder="Marie Dupont" className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Statut</label>
                <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v })}>
                  <SelectTrigger data-testid="asset-status-select" className="mt-1.5 bg-white"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-white border border-slate-200 shadow-lg z-50">
                    {meta.asset_statuses.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Date d'achat</label>
                <input data-testid="asset-date-input" type="date" value={form.purchase_date} onChange={(e) => setForm({ ...form, purchase_date: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => setModal(null)} className="h-10 px-4 rounded-lg border border-slate-200 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">Annuler</button>
            <button data-testid="asset-save-button" onClick={save} className="h-10 px-5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors">Enregistrer</button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
