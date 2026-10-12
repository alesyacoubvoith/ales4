import { useAuth } from "@/context/AuthContext";
import { Headset, LayoutDashboard, Ticket, Boxes, BellRing, ScrollText, PlusCircle, User, UsersRound, MonitorSmartphone } from "lucide-react";

const adminNav = [
  { key: "overview", label: "Tableau de bord", icon: LayoutDashboard },
  { key: "tickets", label: "Tous les tickets", icon: Ticket },
  { key: "inventory", label: "Gestion du stock", icon: Boxes },
  { key: "parc", label: "Parc informatique", icon: MonitorSmartphone },
  { key: "reminders", label: "Alertes & rappels", icon: BellRing },
  { key: "logs", label: "Logs de connexion", icon: ScrollText },
  { key: "accounts", label: "Comptes & accès", icon: UsersRound },
];

const parcItem = { key: "parc", label: "Parc informatique", icon: MonitorSmartphone };

const employeeNav = [
  { key: "mytickets", label: "Mes tickets", icon: Ticket },
  { key: "new", label: "Nouveau ticket", icon: PlusCircle },
  { key: "profile", label: "Mon profil", icon: User },
];

function buildNav(isAdmin, user) {
  if (isAdmin) return adminNav;
  const nav = [...employeeNav];
  if (user?.can_access_parc) nav.splice(2, 0, parcItem);
  return nav;
}

export const Sidebar = ({ active, setActive }) => {
  const { isAdmin, user } = useAuth();
  const nav = buildNav(isAdmin, user);
  return (
    <aside className="hidden lg:flex lg:w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-200">
        <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center">
          <Headset className="h-5 w-5 text-white" />
        </div>
        <div className="leading-tight">
          <div className="font-display font-extrabold text-slate-900 text-sm">Alex & Co</div>
          <div className="text-[10px] text-slate-400 uppercase tracking-wider">Helpdesk & Stock</div>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {nav.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.key;
          return (
            <button
              key={item.key}
              data-testid={`nav-${item.key}`}
              onClick={() => setActive(item.key)}
              className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <Icon className={`h-[18px] w-[18px] ${isActive ? "text-blue-600" : "text-slate-400"}`} />
              {item.label}
            </button>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-200 text-[11px] text-slate-400">
        {isAdmin ? "Mode Support IT" : "Espace employé"}
      </div>
    </aside>
  );
};

export const MobileNav = ({ active, setActive }) => {
  const { isAdmin, user } = useAuth();
  const nav = buildNav(isAdmin, user);
  return (
    <div className="lg:hidden flex gap-1 overflow-x-auto px-3 py-2 bg-white border-b border-slate-200">
      {nav.map((item) => {
        const Icon = item.icon;
        const isActive = active === item.key;
        return (
          <button
            key={item.key}
            data-testid={`mobile-nav-${item.key}`}
            onClick={() => setActive(item.key)}
            className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium whitespace-nowrap ${
              isActive ? "bg-blue-50 text-blue-700" : "text-slate-600"
            }`}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </button>
        );
      })}
    </div>
  );
};
