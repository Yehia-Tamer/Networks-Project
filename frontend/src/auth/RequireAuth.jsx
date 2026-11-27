import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function RequireAuth({ children }) {
  const { token, loading } = useAuth();
  if (loading) return <p style={{ padding: 16 }}>Loading...</p>;
  return token ? children : <Navigate to="/login" replace />;
}
