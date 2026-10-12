import { useState, useEffect, useCallback } from "react";
import { endpoints } from "@/lib/api";
import { formatDate } from "@/lib/ui";
import { StatCard } from "@/components/Bits";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Boxes, AlertTriangle, Plus, Minus, Pencil, Trash2, PackageCheck, PackageX } from "lucide-react";

const emptyForm = { name: "", category: "", quantity: 0, min_threshold: 0, unit: "unité", location: "", maintenance_date: "", notes: "" };

export const InventoryView = () => {
  const [items, setItems] = useState([]);
  const [cats, setCats] = useState([]);
  const [showLow, setShowLow] = useState(false);
  const [modal, setModal] = useState(null); // {mode, item}
  const [form, setForm] = useState(emptyForm);

  const load = useCallback(async () => {
    const r = await endpoints.inventory();
    setItems(r.data);
  }, []);

  useEffect(() => {
    load();
    endpoints.meta().then((r) => setCats(r.data.stock_categories)).catch(() => {});
  }, [load]);

  const lowItems = items.filter((i) => i.quantity <= i.min_threshold);
  const shown = showLow ? lowItems : items;

  const adjust = async (item, delta) => {
    const q = Math.max(0, item.quantity + delta);
    await endpoints.updateItem(item.id, { quantity: q });
    load();
  };

  const openAdd = () => { setForm(emptyForm); setModal({ mode: "add" }); };
  const openEdit = (item) => { setForm({ ...item, maintenance_date: item.maintenance_date || "" }); setModal({ mode: "edit", item }); };

  const save = async () => {
    if (!form.name || !form.category) return toast.error("Nom et catégorie requis");
    const payload = { ...form, quantity: Number(form.quantity), min_threshold: Number(form.min_threshold), maintenance_date: form.maintenance_date || null };
    try {
      if (modal.mode === "add") { await endpoints.createItem(payload); toast.success("Article ajouté"); }
      else { await endpoints.updateItem(modal.item.id, payload); toast.success("Article modifié"); }
      setModal(null); load();
    } catch { toast.error("Erreur"); }
  };

  const remove = async (item) => {
    await endpoints.deleteItem(item.id);
    toast.success("Article supprimé");
    load();
  };

  return (
    <div className="animate-fade-up">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="font-display text-2xl font-bold text-slate-900">Gestion du stock</h2>
          <p className="text-sm text-slate-500">{items.length} articles · {lowItems.length} en alerte</p>
        </div>
        <div className="flex gap-2">
          <button
            data-testid="toggle-low-stock"
            onClick={() => setShowLow(!showLow)}
            className={`h-10 px-4 rounded-lg text-sm font-medium border transition-colors ${showLow ? "bg-amber-50 border-amber-200 text-amber-800" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"}`}
          >
            {showLow ? "Voir tout" : "Stock bas"}
          </button>
          <button data-testid="add-item-button" onClick={openAdd} className="h-10 px-4 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors flex items-center gap-2">
            <Plus className="h-4 w-4" /> Ajouter
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
        <StatCard label="Total articles" value={items.length} icon={Boxes} tone="blue" />
        <StatCard label="En alerte" value={lowItems.length} icon={AlertTriangle} tone="amber" hint="Sous le seuil mini" />
        <StatCard label="Qté totale" value={items.reduce((s, i) => s + i.quantity, 0)} icon={PackageCheck} tone="emerald" />
      </div>

      {lowItems.length > 0 && !showLow && (
        <div className="mb-5 rounded-xl border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800">
            <span className="font-semibold">{lowItems.length} article(s) sous le seuil :</span> {lowItems.map((i) => i.name).join(", ")}.
          </div>
        </div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-600 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold py-3.5 px-4">Article</th>
                <th className="text-left font-semibold py-3.5 px-4 hidden md:table-cell">Catégorie</th>
                <th className="text-left font-semibold py-3.5 px-4 hidden lg:table-cell">Emplacement</th>
                <th className="text-center font-semibold py-3.5 px-4">Quantité</th>
                <th className="text-right font-semibold py-3.5 px-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {shown.map((item) => {
                const low = item.quantity <= item.min_threshold;
                return (
                  <tr key={item.id} data-testid={`inventory-row-${item.id}`} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-800">{item.name}</span>
                        {low && <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 text-[10px] font-semibold"><PackageX className="h-3 w-3" />Bas</span>}
                      </div>
                      <div className="text-xs text-slate-400">Seuil mini: {item.min_threshold}</div>
                    </td>
                    <td className="py-3 px-4 hidden md:table-cell text-slate-600">{item.category}</td>
                    <td className="py-3 px-4 hidden lg:table-cell text-slate-500">{item.location || "—"}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button data-testid={`qty-minus-${item.id}`} onClick={() => adjust(item, -1)} className="h-7 w-7 rounded-md border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-100 transition-colors"><Minus className="h-3.5 w-3.5" /></button>
                        <span className={`w-10 text-center font-mono font-semibold tabular-nums ${low ? "text-rose-600" : "text-slate-800"}`}>{item.quantity}</span>
                        <button data-testid={`qty-plus-${item.id}`} onClick={() => adjust(item, 1)} className="h-7 w-7 rounded-md border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-blue-50 hover:text-blue-600 transition-colors"><Plus className="h-3.5 w-3.5" /></button>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <button data-testid={`edit-item-${item.id}`} onClick={() => openEdit(item)} className="h-8 w-8 rounded-md flex items-center justify-center text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"><Pencil className="h-4 w-4" /></button>
                        <button data-testid={`delete-item-${item.id}`} onClick={() => remove(item)} className="h-8 w-8 rounded-md flex items-center justify-center text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"><Trash2 className="h-4 w-4" /></button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <Dialog open={!!modal} onOpenChange={(o) => !o && setModal(null)}>
        <DialogContent className="bg-white sm:max-w-lg" data-testid="inventory-modal">
          <DialogHeader><DialogTitle className="font-display text-xl">{modal?.mode === "add" ? "Ajouter un article" : "Modifier l'article"}</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-1">
            <div>
              <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Nom</label>
              <input data-testid="item-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Catégorie</label>
              <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                <SelectTrigger data-testid="item-category-select" className="mt-1.5 bg-white"><SelectValue placeholder="Choisir..." /></SelectTrigger>
                <SelectContent className="bg-white border border-slate-200 shadow-lg z-50">
                  {cats.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Quantité</label>
                <input data-testid="item-quantity-input" type="number" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Seuil d'alerte</label>
                <input data-testid="item-threshold-input" type="number" value={form.min_threshold} onChange={(e) => setForm({ ...form, min_threshold: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Emplacement</label>
                <input data-testid="item-location-input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Date maintenance</label>
                <input data-testid="item-maintenance-input" type="date" value={form.maintenance_date} onChange={(e) => setForm({ ...form, maintenance_date: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => setModal(null)} className="h-10 px-4 rounded-lg border border-slate-200 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">Annuler</button>
            <button data-testid="item-save-button" onClick={save} className="h-10 px-5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors">Enregistrer</button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
