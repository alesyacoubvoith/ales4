export const statusStyles = {
  "Nouveau": "bg-blue-50 text-blue-700 border-blue-200",
  "En cours": "bg-indigo-50 text-indigo-700 border-indigo-200",
  "En attente pièce": "bg-amber-50 text-amber-800 border-amber-200",
  "Résolu": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Fermé": "bg-slate-100 text-slate-600 border-slate-200",
};

export const statusDot = {
  "Nouveau": "bg-blue-500",
  "En cours": "bg-indigo-500",
  "En attente pièce": "bg-amber-500",
  "Résolu": "bg-emerald-500",
  "Fermé": "bg-slate-400",
};

export const priorityStyles = {
  "Basse": "bg-slate-100 text-slate-600 border-slate-200",
  "Moyenne": "bg-sky-50 text-sky-700 border-sky-200",
  "Haute": "bg-orange-50 text-orange-700 border-orange-200",
  "Urgente": "bg-rose-50 text-rose-700 border-rose-200",
};

export const formatDate = (iso) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" });
};

export const formatDateTime = (iso) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("fr-FR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
};

export const daysUntil = (dateStr) => {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  const now = new Date();
  return Math.ceil((d - now) / (1000 * 60 * 60 * 24));
};
