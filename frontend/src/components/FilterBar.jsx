import React from "react";

export default function FilterBar({ search, severity, onSearchChange, onSeverityChange }) {
  return (
    <div className="filter-bar">
      <input
        type="search"
        placeholder="Filter by service or text"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
      />
      <select value={severity} onChange={(e) => onSeverityChange(e.target.value)}>
        <option value="">All severities</option>
        <option value="critical">Critical</option>
        <option value="warning">Warning</option>
        <option value="info">Info</option>
      </select>
    </div>
  );
}
