import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import "./auth.css";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      await login(username.trim(), password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Log in</h1>
        <input placeholder="Username" value={username} autoCapitalize="none"
               onChange={(e) => setUsername(e.target.value)} required />
        <input placeholder="Password" type="password" value={password}
               onChange={(e) => setPassword(e.target.value)} required />
        {error && <div className="auth-error">{error}</div>}
        <button disabled={busy}>{busy ? "Logging in..." : "Log in"}</button>
        <div className="auth-link">No account? <Link to="/register">Register</Link></div>
      </form>
    </div>
  );
}
