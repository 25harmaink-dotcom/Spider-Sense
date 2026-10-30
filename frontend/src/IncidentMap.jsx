import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { locationName } from './locations'

export default function IncidentMap({ incidents, loading, role, onSelect }) {
  const valid = incidents.filter(i => Number.isFinite(Number(i.latitude)) && Number.isFinite(Number(i.longitude)) && i.latitude !== null && i.longitude !== null)
  return <section className="panel map-panel" aria-label="Incident map">
    <div className="panel-heading"><div><div className="eyebrow red">CITYWIDE VIEW / NEW YORK</div><h2>{role === 'command' ? 'COMMAND OPERATIONS MAP' : 'PATROL MAP'}</h2><p>{role === 'command' ? 'Showing incidents on the current filtered page.' : 'Showing incidents in the selected mission tab.'} New reports show an approximate neighborhood point, not an exact address.</p></div><span className="count">{valid.length} ON MAP</span></div>
    <MapContainer center={[40.7128, -73.95]} zoom={10} scrollWheelZoom={false} className="incident-map" aria-label="New York incident map">
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {valid.map(i => <CircleMarker key={i.id} center={[i.latitude, i.longitude]} radius={10} pathOptions={{ color: '#fff', weight: 2, fillColor: i.severity >= 4 ? '#e32d3b' : i.severity === 3 ? '#e5ad2b' : '#3aa46b', fillOpacity: 0.95 }}>
        <Popup><strong>{i.title}</strong><br/>Incident #{i.id} · Severity {i.severity}/5<br/>{locationName(i.latitude, i.longitude)}<br/><button type="button" className="map-select" onClick={() => onSelect(i)}>View incident details</button></Popup>
      </CircleMarker>)}
    </MapContainer>
    <div className="map-caption">{loading ? 'Loading incident data…' : valid.length ? 'Select a marker or use the incident list below. Multiple incidents may overlap at the same area.' : 'No incidents in this view yet. The map needs an internet connection for map tiles.'} <span>● Low &nbsp; ● Medium &nbsp; ● High severity</span></div>
  </section>
}
