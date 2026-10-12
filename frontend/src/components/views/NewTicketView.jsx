import { useState, useEffect } from "react";
import { endpoints } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Send } from "lucide-react";

export const NewTicketView = ({ onDone }) => {
  const { user } = useAuth();
  const [meta, setMeta] = useState({ ticket_categories: [], ticket_priorities: [] });
  const [form, setForm] = useState({ title: "", description: "", category: "", priority: "Moyenne" });
  const [saving, setSaving] = useState(false);

  useEffect(() => { endpoints.meta().then((r) => setMeta(r.data)).catch(() => {}); }, []);

  const submit = async () => {
    if (!form.title || !form.description || !form.category || !form.priority) return toast.error("Remplis tous les champs");
    setSaving(true);
    try {
      await endpoints.createTicket({ ...form, creator_id: user.id });
      toast.success("Ticket créé avec succès");
      onDone?.();
    } catch { toast.error("Erreur lors de la création"); } finally { setSaving(false); }
  };

  return (
    <div className="animate-fade-up max-w-2xl">
      <h2 className="font-display text-2xl font-bold text-slate-900">Nouveau ticket</h2>
      <p className="text-sm text-slate-500 mb-5">Décris ton problème, l'équipe support le prendra en charge.</p>
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6 space-y-4">
        <div>
          <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Titre</label>
          <input data-testid="new-ticket-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Ex: PC ne démarre plus" className="mt-1.5 w-full h-11 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
        </div>
        <div>
          <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Description</label>
          <textarea data-testid="new-ticket-description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={4} placeholder="Décris le problème en détail..." className="mt-1.5 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Catégorie</label>
            <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
              <SelectTrigger data-testid="new-ticket-category" className="mt-1.5 bg-white"><SelectValue placeholder="Choisir..." /></SelectTrigger>
              <SelectContent className="bg-white border border-slate-200 shadow-lg z-50">
                {meta.ticket_categories.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Priorité</label>
            <Select value={form.priority} onValueChange={(v) => setForm({ ...form, priority: v })}>
              <SelectTrigger data-testid="new-ticket-priority" className="mt-1.5 bg-white"><SelectValue /></SelectTrigger>
              <SelectContent className="bg-white border border-slate-200 shadow-lg z-50">
                {meta.ticket_priorities.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        <button data-testid="new-ticket-submit" onClick={submit} disabled={saving} className="h-11 px-5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors flex items-center gap-2 disabled:opacity-60">
          <Send className="h-4 w-4" /> Envoyer le ticket
        </button>
      </div>
    </div>
  );
};
