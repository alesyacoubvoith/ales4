import "@/App.css";
import { useAuth } from "@/context/AuthContext";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import { Toaster } from "@/components/ui/sonner";

function App() {
  const { user, ready } = useAuth();
  if (!ready) return <div className="min-h-screen bg-slate-50" />;
  return (
    <div className="App">
      {user ? <Dashboard /> : <Login />}
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
