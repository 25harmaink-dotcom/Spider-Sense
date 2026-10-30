import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import Login from "./Login";

// Backend API URL
const API_URL = "http://127.0.0.1:8000";

// Determine marker color based on severity
function getSeverityColor(severity) {
  if (severity <= 2) return "#22c55e"; // Green
  if (severity === 3) return "#eab308"; // Yellow
  return "#ef4444"; // Red
}

// Create colored map markers
function createMarkerIcon(severity) {
  const color = getSeverityColor(severity);

  return L.divIcon({
    className: "",
    html: `
      <div style="
        background-color: ${color};
        width: 28px;
        height: 28px;
        border: 3px solid white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        box-shadow: 0 2px 6px #000;
      ">
        !
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function App() {
  // Authentication
  const [token, setToken] = useState(null);

  // Incidents from FastAPI
  const [incidents, setIncidents] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Filters
  const [severityFilter, setSeverityFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  // Fetch real incidents when Hero logs in
  useEffect(() => {
    if (!token) {
      return;
    }

    const controller = new AbortController();

    async function fetchIncidents() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch(`${API_URL}/hero/incidents`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        if (response.status === 401 || response.status === 403) {
          throw new Error(
            "Access denied. Please log in with a valid Hero account."
          );
        }

        if (!response.ok) {
          throw new Error("Failed to fetch incidents from the backend.");
        }

        const data = await response.json();

        // Handle array or paginated response
        const incidentList = Array.isArray(data)
          ? data
          : data.items ?? [];

        if (!controller.signal.aborted) {
          setIncidents(incidentList);
        }
      } catch (err) {
        if (err.name !== "AbortError" && !controller.signal.aborted) {
          setError(err.message);
          setIncidents([]);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    fetchIncidents();

    return () => controller.abort();
  }, [token]);

  // Filter incidents
  const filteredIncidents = incidents.filter((incident) => {
    const matchesCategory =
      categoryFilter === "all" ||
      incident.category?.toLowerCase() === categoryFilter.toLowerCase();

    let matchesSeverity = true;

    if (severityFilter === "low") {
      matchesSeverity = incident.severity <= 2;
    } else if (severityFilter === "medium") {
      matchesSeverity = incident.severity === 3;
    } else if (severityFilter === "high") {
      matchesSeverity = incident.severity >= 4;
    }

    return matchesCategory && matchesSeverity;
  });

  // Show login page before authentication
  if (!token) {
    return <Login onLogin={setToken} />;
  }

  // Logout
  function handleLogout() {
    setToken(null);
    setIncidents([]);
    setError("");
    setSeverityFilter("all");
    setCategoryFilter("all");
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        fontFamily: "Arial, sans-serif",
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "20px",
          backgroundColor: "#1e293b",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "24px", color: "#f8fafc" }}>
          🕷️ Spider-Sense Alert System — NYC
        </h1>

        <button
          onClick={handleLogout}
          style={{
            padding: "10px 20px",
            backgroundColor: "#dc2626",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </header>

      {/* Loading message */}
      {loading && (
        <p style={{ textAlign: "center", padding: "10px" }}>
          Loading incidents from FastAPI...
        </p>
      )}

      {/* Error message */}
      {error && (
        <p
          role="alert"
          style={{
            textAlign: "center",
            color: "#fca5a5",
            padding: "10px",
          }}
        >
          {error}
        </p>
      )}

      {/* Filters */}
      <div
        className="filters"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "20px",
          flexWrap: "wrap",
          padding: "15px",
          backgroundColor: "#1e293b",
          color: "#f8fafc",
        }}
      >
        <label>
          Severity:{" "}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              padding: "8px",
              backgroundColor: "#334155",
              color: "white",
              border: "1px solid #475569",
              borderRadius: "5px",
            }}
          >
            <option value="all">All Severities</option>
            <option value="low">Low (1–2)</option>
            <option value="medium">Medium (3)</option>
            <option value="high">High (4–5)</option>
          </select>
        </label>

        <label>
          Category:{" "}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{
              padding: "8px",
              backgroundColor: "#334155",
              color: "white",
              border: "1px solid #475569",
              borderRadius: "5px",
            }}
          >
            <option value="all">All Categories</option>
            <option value="Fire">Fire</option>
            <option value="Accident">Accident</option>
            <option value="Utility">Utility</option>
          </select>
        </label>

        <span>
          Showing {filteredIncidents.length} of {incidents.length} incidents
        </span>
      </div>

      {/* NYC Map */}
      <MapContainer
        center={[40.7128, -74.006]}
        zoom={12}
        style={{
          height: "75vh",
          width: "100%",
        }}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {filteredIncidents
          .filter(
            (incident) =>
              Number.isFinite(Number(incident.latitude)) &&
              Number.isFinite(Number(incident.longitude)) &&
              incident.latitude !== null &&
              incident.longitude !== null
          )
          .map((incident) => (
            <Marker
              key={incident.id}
              position={[
                Number(incident.latitude),
                Number(incident.longitude),
              ]}
              icon={createMarkerIcon(incident.severity)}
            >
              <Popup>
                <strong>{incident.title}</strong>
                <br />
                Category: {incident.category}
                <br />
                Severity: {incident.severity}/5
                <br />
                Status: {incident.status}
              </Popup>
            </Marker>
          ))}
      </MapContainer>

      {/* Footer */}
      <footer
        style={{
          textAlign: "center",
          padding: "15px",
          backgroundColor: "#1e293b",
          color: "#94a3b8",
        }}
      >
        Spider-Sense Alert System | New York City Emergency Monitoring
      </footer>
    </div>
  );
}

export default App;