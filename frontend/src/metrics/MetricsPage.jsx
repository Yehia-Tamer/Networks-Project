import { useEffect, useState } from "react";
import { api } from "../api/client";

const fmtBytes = (n) =>
  n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(2)} MB`;
const fmtTime = (s) =>
  `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m ${s % 60}s`;

export default function MetricsPage() {
  const [m, setM] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    const load = () =>
      api("/metrics")
        .then((d) => { if (alive) { setM(d); setError(""); } })
        .catch((e) => alive && setError(e.message));
    load();
    const id = setInterval(load, 2000); // refresh every 2 seconds
    return () => { alive = false; clearInterval(id); };
  }, []);

  const cards = m && [
    ["Active connections", m.active_connections],
    ["Messages / second", m.messages_per_second],
    ["Bytes / second", fmtBytes(m.bytes_per_second)],
    ["Messages in", m.messages_in],
    ["Messages out", m.messages_out],
    ["Bytes in", fmtBytes(m.bytes_in)],
    ["Bytes out", fmtBytes(m.bytes_out)],
    ["Uptime", fmtTime(m.uptime_seconds)],
  ];

  return (
    <div style={{ padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: 22 }}>Live metrics</h1>
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}
      {!m && !error && <p>Loading...</p>}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 12 }}>
        {cards?.map(([label, value]) => (
          <div key={label} style={{ background: "#f2f4f7", borderRadius: 12, padding: 14 }}>
            <div style={{ fontSize: 13, color: "#555" }}>{label}</div>
            <div style={{ fontSize: 24, fontWeight: 600 }}>{value}</div>
          </div>
        ))}
      </div>
      <p style={{ fontSize: 12, color: "#777" }}>Updates every 2 seconds.</p>
    </div>
  );
}
