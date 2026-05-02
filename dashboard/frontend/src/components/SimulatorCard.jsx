import { useMemo } from 'react'

function SimulatorCard({ simulator }) {
  const {
    name,
    is_online,
    lat,
    lon,
    altitude_ft,
    speed_kts,
    heading,
    closest_airport,
    airport_distance_nm,
    packet_count,
  } = simulator

  // Format coordinates for display
  const formatCoord = (value, isLat) => {
    const dir = isLat ? (value >= 0 ? 'N' : 'S') : (value >= 0 ? 'E' : 'W')
    return `${Math.abs(value).toFixed(4)}° ${dir}`
  }

  // Format heading with cardinal direction
  const formatHeading = (hdg) => {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    const index = Math.round(hdg / 45) % 8
    return `${hdg}° ${directions[index]}`
  }

  return (
    <div
      className={`rounded-xl shadow-lg overflow-hidden transition-all duration-300 ${
        is_online
          ? 'bg-white border-2 border-green-400 status-online'
          : 'bg-gray-100 border-2 border-gray-300 opacity-75'
      }`}
    >
      {/* Header */}
      <div
        className={`px-4 py-3 ${
          is_online
            ? 'bg-gradient-to-r from-green-500 to-green-600'
            : 'bg-gradient-to-r from-gray-400 to-gray-500'
        }`}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">{name}</h2>
          <span
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              is_online
                ? 'bg-white text-green-600'
                : 'bg-gray-200 text-gray-600'
            }`}
          >
            {is_online ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 space-y-4">
        {/* Position Section */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Latitude
            </label>
            <p className="text-lg font-semibold text-gray-900">
              {is_online ? formatCoord(lat, true) : '---'}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Longitude
            </label>
            <p className="text-lg font-semibold text-gray-900">
              {is_online ? formatCoord(lon, false) : '---'}
            </p>
          </div>
        </div>

        {/* Flight Data Section */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <label className="text-xs font-medium text-blue-600 uppercase tracking-wide">
              Altitude
            </label>
            <p className="text-xl font-bold text-blue-900">
              {is_online ? altitude_ft.toLocaleString() : '---'}
            </p>
            <span className="text-xs text-blue-600">ft MSL</span>
          </div>
          <div className="bg-purple-50 rounded-lg p-3 text-center">
            <label className="text-xs font-medium text-purple-600 uppercase tracking-wide">
              Airspeed
            </label>
            <p className="text-xl font-bold text-purple-900">
              {is_online ? speed_kts : '---'}
            </p>
            <span className="text-xs text-purple-600">kts</span>
          </div>
          <div className="bg-orange-50 rounded-lg p-3 text-center">
            <label className="text-xs font-medium text-orange-600 uppercase tracking-wide">
              Heading
            </label>
            <p className="text-xl font-bold text-orange-900">
              {is_online ? formatHeading(heading) : '---'}
            </p>
          </div>
        </div>

        {/* Nearest Airport Section */}
        <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-3">
          <label className="text-xs font-medium text-primary-600 uppercase tracking-wide">
            Nearest Airport
          </label>
          {is_online && closest_airport ? (
            <div className="mt-1">
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-primary-900">
                  {closest_airport.icao}
                </span>
                <span className="text-lg font-semibold text-primary-700">
                  {airport_distance_nm} NM
                </span>
              </div>
              <p className="text-sm text-primary-700 truncate">
                {closest_airport.name}
              </p>
            </div>
          ) : (
            <p className="text-lg font-semibold text-gray-400 mt-1">---</p>
          )}
        </div>

        {/* Packets Counter */}
        <div className="flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-gray-100">
          <span>Port: {simulator.port}</span>
          <span>Packets: {packet_count.toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}

export default SimulatorCard
