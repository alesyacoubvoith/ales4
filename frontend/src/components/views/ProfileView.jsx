import { useAuth } from "@/context/AuthContext";
import { User, Badge as BadgeIcon, LogOut } from "lucide-react";

export const ProfileView = () => {
  const { user, logout } = useAuth();
  return (
    <div className="animate-fade-up max-w-xl">
      <h2 className="font-display text-2xl font-bold text-slate-900 mb-5">Mon profil</h2>
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6">
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded-2xl bg-blue-600 flex items-center justify-center text-white text-xl font-bold">
            {user.name.split(" ").map((p) => p[0]).join("").slice(0, 2)}
          </div>
          <div>
            <div className="font-display text-xl font-bold text-slate-900">{user.name}</div>
            <div className="text-sm text-slate-500">{user.title}</div>
          </div>
        </div>
        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-500">ID Employé</div>
            <div className="mt-1 font-mono text-slate-800">{user.id}</div>
          </div>
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-500">Rôle</div>
            <div className="mt-1 text-slate-800">{user.role === "admin" ? "Support IT Admin" : "Employé"}</div>
          </div>
        </div>
        <button data-testid="profile-logout" onClick={logout} className="mt-6 h-10 px-4 rounded-lg border border-rose-200 text-rose-600 text-sm font-medium hover:bg-rose-50 transition-colors flex items-center gap-2">
          <LogOut className="h-4 w-4" /> Se déconnecter
        </button>
      </div>
    </div>
  );
};
