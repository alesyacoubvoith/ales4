import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Header } from "@/components/Header";
import { Sidebar, MobileNav } from "@/components/Sidebar";
import { TicketModal } from "@/components/TicketModal";
import { OverviewView } from "@/components/views/OverviewView";
import { TicketsView } from "@/components/views/TicketsView";
import { InventoryView } from "@/components/views/InventoryView";
import { RemindersView } from "@/components/views/RemindersView";
import { LogsView } from "@/components/views/LogsView";
import { AccountsView } from "@/components/views/AccountsView";
import { ProfileView } from "@/components/views/ProfileView";
import { NewTicketView } from "@/components/views/NewTicketView";

export default function Dashboard() {
  const { isAdmin } = useAuth();
  const [active, setActive] = useState(isAdmin ? "overview" : "mytickets");
  const [modalOpen, setModalOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const render = () => {
    switch (active) {
      case "overview": return <OverviewView setActive={setActive} />;
      case "tickets": return <TicketsView key={refreshKey} adminMode />;
      case "inventory": return <InventoryView />;
      case "reminders": return <RemindersView />;
      case "logs": return <LogsView />;
      case "accounts": return <AccountsView />;
      case "mytickets": return <TicketsView key={refreshKey} adminMode={false} />;
      case "new": return <NewTicketView onDone={() => { setRefreshKey((k) => k + 1); setActive("mytickets"); }} />;
      case "profile": return <ProfileView />;
      default: return null;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar active={active} setActive={setActive} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onNewTicket={() => setModalOpen(true)} />
        <MobileNav active={active} setActive={setActive} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          {render()}
        </main>
      </div>
      <TicketModal open={modalOpen} onClose={() => setModalOpen(false)} onCreated={() => setRefreshKey((k) => k + 1)} />
    </div>
  );
}
