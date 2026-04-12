import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import "../utils/fixLeaflet";

function buildMarker(severity, blinking) {
  const tone = {
    SAFE: "#22c55e",
    WARNING: "#facc15",
    DANGER: "#f97316",
    CRITICAL: "#ef4444",
  }[String(severity || "SAFE").toUpperCase()] || "#22c55e";

  return L.divIcon({
    className: "hotspot-map-marker-shell",
    html: `<span class="hotspot-map-marker ${blinking ? "blinking" : ""}" style="--marker-color:${tone};"></span>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

export default function HotspotMap({ locations = [], selectedLocation, fallbackMessage = "Live data temporarily unavailable" }) {
  const activeLocations = Array.isArray(locations) ? locations : [];
  const center = selectedLocation
    ? [selectedLocation.lat, selectedLocation.lng]
    : activeLocations[0]
      ? [activeLocations[0].lat, activeLocations[0].lng]
      : [12.9716, 77.5946];

  return (
    <section className="hotspot-map-panel">
      <div className="hotspot-map-panel__header">
        <div>
          <p>Hotspot Monitoring Grid</p>
          <h3>Location-aware risk map</h3>
        </div>
        <span>{selectedLocation?.last_updated_label || fallbackMessage}</span>
      </div>
      <div className="hotspot-map-panel__canvas">
        <MapContainer center={center} zoom={11} scrollWheelZoom={false} className="hotspot-map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {activeLocations.map((location) => (
            <Marker
              key={`${location.id}-${location.name}`}
              position={[location.lat, location.lng]}
              icon={buildMarker(location.severity, location.marker_blinking)}
            >
              <Popup>
                <div className="hotspot-map-popup">
                  <strong>{location.name}</strong>
                  <p>{location.severity} • {location.priority}</p>
                  <small>{location.last_updated_label}</small>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
      <div className="hotspot-map-panel__legend">
        <span className="safe">Safe</span>
        <span className="warning">Warning</span>
        <span className="danger">Danger</span>
        <span className="critical">Critical</span>
      </div>
    </section>
  );
}
