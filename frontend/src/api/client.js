// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// client.js
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

const API_BASE = '/api'

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`

  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  // Auth
  login: (username, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  logout: () =>
    request('/auth/logout', { method: 'POST' }),
  checkAuth: () =>
    request('/auth/check'),

  // Status
  getStatus: () =>
    request('/status'),

  // Control
  start: () =>
    request('/control', { method: 'POST', body: JSON.stringify({ action: 'start' }) }),
  stop: () =>
    request('/control', { method: 'POST', body: JSON.stringify({ action: 'stop' }) }),

  // Position
  updatePosition: (data) =>
    request('/position', { method: 'POST', body: JSON.stringify(data) }),

  // Config
  updateModes: (modes) =>
    request('/config/modes', { method: 'POST', body: JSON.stringify(modes) }),
  updateNetwork: (network) =>
    request('/config/network', { method: 'POST', body: JSON.stringify(network) }),
  updateNmea: (nmea) =>
    request('/config/nmea', { method: 'POST', body: JSON.stringify(nmea) }),
  updateSerial: (serial) =>
    request('/config/serial', { method: 'POST', body: JSON.stringify(serial) }),

  // Serial
  listDevices: () =>
    request('/serial/devices'),
  selectDevice: (device) =>
    request('/serial/select', { method: 'POST', body: JSON.stringify({ device }) }),

  // Airports
  lookupAirport: (icao) =>
    request(`/airports/lookup/${icao}`),
  searchAirports: (query, limit = 10) =>
    request(`/airports/search?q=${encodeURIComponent(query)}&limit=${limit}`),
  listAirports: () =>
    request('/airports/list'),
}
