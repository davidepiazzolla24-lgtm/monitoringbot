import React, { useEffect, useMemo, useState } from "react";
import FilterBar from "../components/FilterBar";

export default function Timeline({ role }) {
  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");

  useEffect(() => {
    fetch("/timeline", {
      headers: { Authorization: `Bearer ${role === "admin" ? "admin-token" : "viewer-token"}` },
    })
      .then((res) => res.json())
      .then((data) => setEvents(data))
      .catch(() => setEvents([]));
  }, [role]);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:4173/ws/events");
    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setEvents((prev) => [parsed, ...prev]);
      } catch (e) {
        console.error("Failed to parse websocket event", e);
      }
    };
    return () => ws.close();
  }, []);

  const filtered = useMemo(() => {
    const term = search.toLowerCase();
    return events
      .filter((evt) =>
        [evt.service, evt.message, evt.level].some((part) => part?.toLowerCase().includes(term))
      )
      .filter((evt) => (severity ? evt.level === severity : true));
  }, [events, search, severity]);

  return (
    <section>
      <FilterBar search={search} severity={severity} onSearchChange={setSearch} onSeverityChange={setSeverity} />
      <table className="table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Service</th>
            <th>Level</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((evt) => (
            <tr key={evt.id}>
              <td>{new Date(evt.timestamp).toLocaleString()}</td>
              <td>{evt.service}</td>
              <td>{evt.level}</td>
              <td>{evt.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
