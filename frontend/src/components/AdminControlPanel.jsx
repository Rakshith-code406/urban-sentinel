export default function AdminControlPanel({
  alerts = [],
  loading = false,
  onResolve,
  onAssign,
  onForceReset,
  selectedLocationLabel,
}) {
  return (
    <section className="admin-control-panel">
      <div className="admin-control-panel__header">
        <div>
          <p>Admin Control Panel</p>
          <h3>Operational response console</h3>
        </div>
        <button type="button" onClick={onForceReset} disabled={loading}>
          Force reset sensor
        </button>
      </div>
      <p className="admin-control-panel__meta">
        {selectedLocationLabel ? `Monitoring ${selectedLocationLabel}` : "Select a monitored area"}.
        Resolve alerts, assign departments, and review the latest state changes.
      </p>
      <div className="admin-control-panel__list">
        {alerts.length ? (
          alerts.slice(0, 5).map((alert) => (
            <article key={alert.id} className="admin-alert-card">
              <div>
                <strong>{alert.sensor_label}</strong>
                <p>{alert.location || "Monitored zone"} • {alert.severity} • {alert.priority}</p>
                <small>{alert.note || "No note attached."}</small>
              </div>
              <div className="admin-alert-card__actions">
                <button type="button" onClick={() => onAssign(alert.id)} disabled={loading}>
                  Assign dept
                </button>
                <button type="button" onClick={() => onResolve(alert.id)} disabled={loading}>
                  Resolve alert
                </button>
              </div>
            </article>
          ))
        ) : (
          <p className="admin-control-panel__empty">No active monitoring alerts right now.</p>
        )}
      </div>
    </section>
  );
}
