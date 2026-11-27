import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import "./auth.css";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [f, setF] = useState({ username: "", email: "", display_name: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      await register({ ...f, username: f.username.trim() });
      navigate("/");
    } catch (err) {
      setError(err.message || "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Create account</h1>
        <input placeholder="Username" value={f.username} autoCapitalize="none" onChange={set("username")} required />
        <input placeholder="Display name" value={f.display_name} onChange={set("display_name")} required />
        <input placeholder="Email" type="email" value={f.email} onChange={set("email")} required />
        <input placeholder="Password" type="password" minLength={8} value={f.password} onChange={set("password")} required />
        {error && <div className="auth-error">{error}</div>}
        <button disabled={busy}>{busy ? "Creating..." : "Register"}</button>
        <div className="auth-link">Have an account? <Link to="/login">Log in</Link></div>
      </form>
    </div>
  );
}
