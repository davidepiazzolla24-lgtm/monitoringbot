import React, { useEffect, useMemo, useState } from "react";
import FilterBar from "../components/FilterBar";

export default function Incidents({ role, onRoleChange }) {
  const [incidents, setIncidents] = useState([]);
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");

  const headers = {
    Authorization: `Bearer ${role === "admin" ? "admin-token" : "viewer-token"}`,
    "Content-Type": "application/json",
  };

  const loadIncidents = () => {
    fetch("/incidents", { headers })
      .then((res) => res.json())
      .then((data) => setIncidents(data))
      .catch(() => setIncidents([]));
  };

  useEffect(() => {
    loadIncidents();
  }, [role]);

  const filtered = useMemo(() => {
    const term = search.toLowerCase();
    return incidents
      .filter((inc) =>
        [inc.service, inc.summary, inc.impact].some((part) => part?.toLowerCase().includes(term))
      )
      .filter((inc) => (severity ? inc.impact === severity : true));
  }, [incidents, search, severity]);

  const create = () => {
    const service = prompt("Service?");
    const summary = prompt("Summary?");
    const impact = prompt("Impact?");
    if (!service || !summary) return;
    fetch("/incidents", {
      method: "POST",
      headers,
      body: JSON.stringify({ service, summary, impact: impact || "unknown" }),
    }).then(loadIncidents);
  };

  const close = (id) => {
    fetch(`/incidents/${id}/close`, { method: "PATCH", headers }).then(loadIncidents);
  };

  return (
    <section>
      <FilterBar search={search} severity={severity} onSearchChange={setSearch} onSeverityChange={setSeverity} />
      <div style={{ marginBottom: "1rem" }}>
        <label>
          Role:
          <select value={role} onChange={(e) => onRoleChange(e.target.value)} style={{ marginLeft: "0.5rem" }}>
            <option value="viewer">Viewer</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        {role === "admin" && (
          <button style={{ marginLeft: "1rem" }} onClick={create}>
            Create incident
          </button>
        )}
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Service</th>
            <th>Summary</th>
            <th>Impact</th>
            <th>Opened</th>
            <th>Closed</th>
            {role === "admin" && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {filtered.map((inc) => (
            <tr key={inc.id}>
              <td>{inc.id}</td>
              <td>{inc.service}</td>
              <td>{inc.summary}</td>
              <td>{inc.impact}</td>
              <td>{new Date(inc.opened_at).toLocaleString()}</td>
              <td>{inc.closed_at ? new Date(inc.closed_at).toLocaleString() : "Open"}</td>
              {role === "admin" && (
                <td>
                  {!inc.closed_at && <button onClick={() => close(inc.id)}>Close</button>}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
