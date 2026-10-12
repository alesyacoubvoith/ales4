import { useState, useEffect, useCallback } from "react";
import { endpoints } from "@/lib/api";
import { formatDate, daysUntil } from "@/lib/ui";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { BellRing, Plus, Trash2, CalendarClock, Check } from "lucide-react";

export const RemindersView = () => {
  const [reminders, setReminders] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: "", due_date: "", category: "Maintenance", notes: "" });

  const load = useCallback(async () => {
    const r = await endpoints.reminders();
    setReminders(r.data);
  }, []);

  useEffect(() => { load(); }, [load]);

  const save = async () => {
    if (!form.title || !form.due_date) return toast.error("Titre et date requis");
    await endpoints.createReminder(form);
    toast.success("Rappel ajouté");
    setForm({ title: "", due_date: "", category: "Maintenance", notes: "" });
    setOpen(false);
    load();
  };

  const toggle = async (r) => { await endpoints.toggleReminder(r.id); load(); };
  const remove = async (r) => { await endpoints.deleteReminder(r.id); toast.success("Rappel supprimé"); load(); };

  const urgency = (days, done) => {
    if (done) return "border-slate-200 bg-slate-50";
    if (days < 0) return "border-rose-200 bg-rose-50";
    if (days <= 7) return "border-amber-200 bg-amber-50";
    return "border-slate-200 bg-white";
  };

  return (
    <div className="animate-fade-up">
      <div className="flex items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="font-display text-2xl font-bold text-slate-900">Alertes & rappels</h2>
          <p className="text-sm text-slate-500">Échéances de maintenance, licences et garanties</p>
        </div>
        <button data-testid="add-reminder-button" onClick={() => setOpen(true)} className="h-10 px-4 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors flex items-center gap-2">
          <Plus className="h-4 w-4" /> Rappel
        </button>
      </div>

      <div className="space-y-3">
        {reminders.map((r) => {
          const days = daysUntil(r.due_date);
          return (
            <div key={r.id} data-testid={`reminder-${r.id}`} className={`rounded-xl border p-4 flex items-center gap-4 transition-colors ${urgency(days, r.done)}`}>
              <button
                data-testid={`reminder-toggle-${r.id}`}
                onClick={() => toggle(r)}
                className={`h-9 w-9 rounded-lg shrink-0 flex items-center justify-center border transition-colors ${r.done ? "bg-emerald-500 border-emerald-500 text-white" : "bg-white border-slate-300 text-transparent hover:border-blue-400"}`}
              >
                <Check className="h-4 w-4" />
              </button>
              <div className="flex-1 min-w-0">
                <div className={`font-semibold ${r.done ? "text-slate-400 line-through" : "text-slate-800"}`}>{r.title}</div>
                <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                  <CalendarClock className="h-3.5 w-3.5" />
                  {formatDate(r.due_date)}
                  <span className="rounded bg-white/70 border border-slate-200 px-1.5 py-0.5">{r.category}</span>
                </div>
              </div>
              {!r.done && (
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${days < 0 ? "bg-rose-100 text-rose-700" : days <= 7 ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-600"}`}>
                  {days < 0 ? `En retard de ${Math.abs(days)}j` : days === 0 ? "Aujourd'hui" : `Dans ${days}j`}
                </span>
              )}
              <button data-testid={`reminder-delete-${r.id}`} onClick={() => remove(r)} className="h-8 w-8 rounded-md flex items-center justify-center text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"><Trash2 className="h-4 w-4" /></button>
            </div>
          );
        })}
        {reminders.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center text-slate-400">
            <BellRing className="h-8 w-8 mx-auto mb-2 text-slate-300" />Aucun rappel
          </div>
        )}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="bg-white sm:max-w-md" data-testid="reminder-modal">
          <DialogHeader><DialogTitle className="font-display text-xl">Nouveau rappel</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-1">
            <div>
              <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Titre</label>
              <input data-testid="reminder-title-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Ex: Maintenance serveur" className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Date</label>
                <input data-testid="reminder-date-input" type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Catégorie</label>
                <input data-testid="reminder-category-input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => setOpen(false)} className="h-10 px-4 rounded-lg border border-slate-200 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">Annuler</button>
            <button data-testid="reminder-save-button" onClick={save} className="h-10 px-5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors">Ajouter</button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
