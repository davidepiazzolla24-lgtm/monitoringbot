import React, { useMemo, useState } from "react";
import Status from "./pages/Status";
import Timeline from "./pages/Timeline";
import Incidents from "./pages/Incidents";
import Settings from "./pages/Settings";

const PAGES = ["Status", "Timeline", "Incidents", "Settings"];

export default function App() {
  const [page, setPage] = useState("Status");
  const [role, setRole] = useState("viewer");

  const currentPage = useMemo(() => {
    switch (page) {
      case "Timeline":
        return <Timeline role={role} />;
      case "Incidents":
        return <Incidents role={role} onRoleChange={setRole} />;
      case "Settings":
        return <Settings role={role} onRoleChange={setRole} />;
      case "Status":
      default:
        return <Status role={role} />;
    }
  }, [page, role]);

  return (
    <div className="app-shell">
      <header>
        <h1>Monitoring Bot</h1>
        <p>Minimal console for status, incidents, and alert rules.</p>
      </header>
      <nav>
        {PAGES.map((p) => (
          <button key={p} className={page === p ? "active" : ""} onClick={() => setPage(p)}>
            {p}
          </button>
        ))}
      </nav>
      {currentPage}
    </div>
  );
}
