import "@/App.css";
import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { endpoints } from "@/lib/api";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Onboarding from "@/pages/Onboarding";
import { Toaster } from "@/components/ui/sonner";

function App() {
  const { user, ready } = useAuth();
  const [setupNeeded, setSetupNeeded] = useState(null);

  useEffect(() => {
    if (!user) {
      endpoints.setupNeeded().then((r) => setSetupNeeded(r.data.needed)).catch(() => setSetupNeeded(false));
    }
  }, [user]);

  const splash = <div className="min-h-screen bg-slate-50" />;
  if (!ready) return splash;

  let content;
  if (user) content = <Dashboard />;
  else if (setupNeeded === null) content = splash;
  else if (setupNeeded) content = <Onboarding onDone={() => setSetupNeeded(false)} />;
  else content = <Login />;

  return (
    <div className="App">
      {content}
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
