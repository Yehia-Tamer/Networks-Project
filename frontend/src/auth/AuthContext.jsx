import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, getToken, setToken, clearToken } from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(getToken());
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!getToken());

  useEffect(() => {
    if (!token) { setUser(null); setLoading(false); return; }
    api("/users/me")
      .then(setUser)
      .catch(() => { clearToken(); setTokenState(null); })
      .finally(() => setLoading(false));
  }, [token]);

  const login = useCallback(async (username, password) => {
    const data = await api("/auth/login", { method: "POST", form: true, body: { username, password } });
    setToken(data.access_token);
    setTokenState(data.access_token);
  }, []);

  const register = useCallback(async (fields) => {
    await api("/auth/register", { method: "POST", body: fields });
    await login(fields.username, fields.password);
  }, [login]);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
