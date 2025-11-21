import React, { useEffect, useMemo, useState } from "react";
import FilterBar from "../components/FilterBar";

const statusBadge = (status) => `badge ${status}`;

export default function Status({ role }) {
  const [services, setServices] = useState([]);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("service");

  useEffect(() => {
    fetch("/status", {
      headers: {
        Authorization: `Bearer ${role === "admin" ? "admin-token" : "viewer-token"}`,
      },
    })
      .then((res) => res.json())
      .then((data) => setServices(data))
      .catch(() => setServices([]));
  }, [role]);

  const filtered = useMemo(() => {
    const term = search.toLowerCase();
    return [...services]
      .filter((item) => item.service.toLowerCase().includes(term))
      .sort((a, b) => {
        if (sort === "service") return a.service.localeCompare(b.service);
        return new Date(b.updated_at) - new Date(a.updated_at);
      });
  }, [services, search, sort]);

  return (
    <section>
      <div className="filter-bar">
        <FilterBar search={search} severity="" onSearchChange={setSearch} onSeverityChange={() => {}} />
        <button onClick={() => setSort(sort === "service" ? "updated_at" : "service")}>
          Sort by {sort === "service" ? "last update" : "name"}
        </button>
      </div>
      <div className="card-grid">
        {filtered.map((service) => (
          <div className="card" key={service.service}>
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong>{service.service}</strong>
              <span className={statusBadge(service.status)}>{service.status}</span>
            </header>
            <p>{service.details || "No additional details"}</p>
            <small>Updated: {new Date(service.updated_at).toLocaleString()}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
