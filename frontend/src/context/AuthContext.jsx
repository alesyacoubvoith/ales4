import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("helpdesk_user");
    if (stored) setUser(JSON.parse(stored));
    setReady(true);
  }, []);

  const login = (u) => {
    setUser(u);
    localStorage.setItem("helpdesk_user", JSON.stringify(u));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("helpdesk_user");
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, ready, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
