import { useAuth } from "@/context/AuthContext";
import { Headset, LogOut } from "lucide-react";

export const Header = ({ onNewTicket }) => {
  const { user, logout, isAdmin } = useAuth();
  return (
    <header className="h-16 shrink-0 bg-white/90 backdrop-blur-md border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center lg:hidden">
          <Headset className="h-5 w-5 text-white" />
        </div>
        <div className="hidden sm:flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-slate-500">Système opérationnel</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          data-testid="header-new-ticket-button"
          onClick={onNewTicket}
          className="h-9 px-4 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] transition-colors"
        >
          + Nouveau ticket
        </button>
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-200">
          <div className={`h-9 w-9 rounded-full flex items-center justify-center text-white text-xs font-bold ${isAdmin ? "bg-blue-600" : "bg-slate-400"}`}>
            {user.name.split(" ").map((p) => p[0]).join("").slice(0, 2)}
          </div>
          <div className="hidden sm:block leading-tight">
            <div className="text-sm font-semibold text-slate-800">{user.name}</div>
            <div className="text-[11px] text-slate-500">{isAdmin ? "Support Tech Admin" : "Employé"}</div>
          </div>
          <button
            data-testid="logout-button"
            onClick={logout}
            className="ml-1 h-9 w-9 rounded-lg flex items-center justify-center text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
            title="Déconnexion"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
