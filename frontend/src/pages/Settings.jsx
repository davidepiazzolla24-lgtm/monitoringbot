import React, { useEffect, useState } from "react";

export default function Settings({ role, onRoleChange }) {
  const [rules, setRules] = useState([]);

  useEffect(() => {
    fetch("/rules", { headers: { Authorization: `Bearer ${role === "admin" ? "admin-token" : "viewer-token"}` } })
      .then((res) => res.json())
      .then((data) => setRules(data))
      .catch(() => setRules([]));
  }, [role]);

  return (
    <section>
      <h2>Account</h2>
      <p>Signed in as <strong>{role}</strong>. Switch roles to preview RBAC-bound UI controls.</p>
      <select value={role} onChange={(e) => onRoleChange(e.target.value)}>
        <option value="viewer">Viewer</option>
        <option value="admin">Admin</option>
      </select>

      <h2>Alert Rules</h2>
      <div className="card-grid">
        {rules.map((rule) => (
          <div className="card" key={rule.id}>
            <header style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{rule.name}</strong>
              <span className="badge info">{rule.severity}</span>
            </header>
            <p>{rule.description}</p>
            <pre style={{ whiteSpace: "pre-wrap" }}>{rule.expression}</pre>
            <small>{rule.enabled ? "Enabled" : "Disabled"}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
