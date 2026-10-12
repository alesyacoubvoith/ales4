import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { endpoints } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import { Paperclip, X } from "lucide-react";

export const TicketModal = ({ open, onClose, onCreated }) => {
  const { user } = useAuth();
  const [meta, setMeta] = useState({ ticket_categories: [], ticket_priorities: [] });
  const [form, setForm] = useState({ title: "", description: "", category: "", priority: "Moyenne" });
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    endpoints.meta().then((r) => setMeta(r.data)).catch(() => {});
  }, []);

  const submit = async () => {
    if (!form.title || !form.description || !form.category || !form.priority) {
      return toast.error("Remplis tous les champs");
    }
    setSaving(true);
    try {
      let attachment = null;
      if (file) {
        const fd = new FormData();
        fd.append("file", file);
        const up = await endpoints.uploadFile(fd);
        attachment = up.data;
      }
      await endpoints.createTicket({ ...form, creator_id: user.id, attachment });
      toast.success("Ticket créé avec succès");
      setForm({ title: "", description: "", category: "", priority: "Moyenne" });
      setFile(null);
      onCreated?.();
      onClose();
    } catch {
      toast.error("Erreur lors de la création");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="bg-white sm:max-w-lg" data-testid="ticket-modal">
        <DialogHeader>
          <DialogTitle className="font-display text-xl">Nouveau ticket de support</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 mt-2">
          <div>
            <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Titre</label>
            <input
              data-testid="ticket-title-input"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Ex: PC ne démarre plus"
              className="mt-1.5 w-full h-10 rounded-lg border border-slate-200 px-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Description</label>
            <textarea
              data-testid="ticket-description-input"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              placeholder="Décris le problème en détail..."
              className="mt-1.5 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Catégorie</label>
              <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                <SelectTrigger data-testid="ticket-category-select" className="mt-1.5 bg-white">
                  <SelectValue placeholder="Choisir..." />
                </SelectTrigger>
                <SelectContent className="bg-white border border-slate-200 shadow-lg z-50">
                  {meta.ticket_categories.map((c) => (
                    <SelectItem key={c} value={c} data-testid={`ticket-category-${c}`}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Priorité</label>
              <Select value={form.priority} onValueChange={(v) => setForm({ ...form, priority: v })}>
                <SelectTrigger data-testid="ticket-priority-select" className="mt-1.5 bg-white">
                  <SelectValue placeholder="Choisir..." />
                </SelectTrigger>
                <SelectContent className="bg-white border border-slate-200 shadow-lg z-50">
                  {meta.ticket_priorities.map((p) => (
                    <SelectItem key={p} value={p} data-testid={`ticket-priority-${p}`}>{p}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">Pièce jointe (optionnel)</label>
            {file ? (
              <div className="mt-1.5 flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                <span className="flex items-center gap-2 text-sm text-slate-700 truncate"><Paperclip className="h-4 w-4 text-slate-400" />{file.name}</span>
                <button type="button" data-testid="ticket-modal-remove-file" onClick={() => setFile(null)} className="text-slate-400 hover:text-rose-600"><X className="h-4 w-4" /></button>
              </div>
            ) : (
              <label className="mt-1.5 flex items-center gap-2 rounded-lg border border-dashed border-slate-300 px-3 py-2.5 text-sm text-slate-500 cursor-pointer hover:border-blue-400 hover:text-blue-600 transition-colors">
                <Paperclip className="h-4 w-4" /> Ajouter un fichier
                <input data-testid="ticket-modal-file" type="file" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              </label>
            )}
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={onClose} className="h-10 px-4 rounded-lg border border-slate-200 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">Annuler</button>
          <button
            data-testid="ticket-submit-button"
            onClick={submit}
            disabled={saving}
            className="h-10 px-5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors disabled:opacity-60"
          >
            Créer le ticket
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
