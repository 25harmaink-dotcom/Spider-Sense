// Fixed illustrative neighborhood center points, NOT exact incident locations.
export const NYC_LOCATIONS = [
  { name: 'Manhattan — Times Square', lat: 40.7580, lng: -73.9855 },
  { name: 'Manhattan — Central Park', lat: 40.7829, lng: -73.9654 },
  { name: 'Manhattan — Harlem', lat: 40.8116, lng: -73.9465 },
  { name: 'Manhattan — Financial District', lat: 40.7074, lng: -74.0113 },
  { name: 'Manhattan — Lower East Side', lat: 40.7150, lng: -73.9843 },
  { name: 'Brooklyn — Downtown Brooklyn', lat: 40.6932, lng: -73.9896 },
  { name: 'Brooklyn — Williamsburg', lat: 40.7081, lng: -73.9571 },
  { name: 'Brooklyn — Coney Island', lat: 40.5749, lng: -73.9850 },
  { name: 'Brooklyn — Park Slope', lat: 40.6710, lng: -73.9814 },
  { name: 'Queens — Astoria', lat: 40.7644, lng: -73.9235 },
  { name: 'Queens — Flushing', lat: 40.7675, lng: -73.8331 },
  { name: 'Queens — Jamaica', lat: 40.7027, lng: -73.7890 },
  { name: 'Bronx — Fordham', lat: 40.8614, lng: -73.8900 },
  { name: 'Bronx — South Bronx', lat: 40.8168, lng: -73.9170 },
  { name: 'Staten Island — St. George', lat: 40.6437, lng: -74.0736 },
  { name: 'Staten Island — New Dorp', lat: 40.5730, lng: -74.1165 },
]
export function locationName(lat, lng) {
  const point = NYC_LOCATIONS.find(p => Math.abs(p.lat - Number(lat)) < 0.00001 && Math.abs(p.lng - Number(lng)) < 0.00001)
  return point ? `${point.name} (approximate area)` : `Coordinates: ${lat}, ${lng} (previous report)`
}
