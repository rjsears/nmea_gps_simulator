import HealthChain from './HealthChain'

function SimulatorCard({ simulator, showHealth = false }) {
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

  // Health status for header badge
  const getHealthStatus = () => {
    if (!showHealth) return null
    const { emulator_online, sim_reachable, is_online } = simulator
    if (is_online) return { text: 'ALL OK', color: 'bg-white text-green-600' }
    if (!emulator_online) return { text: 'ISSUE', color: 'bg-white text-red-600' }
    if (!sim_reachable) return { text: 'ISSUE', color: 'bg-white text-red-600' }
    return { text: 'ISSUE', color: 'bg-white text-red-600' }
  }
  const healthStatus = getHealthStatus()

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

  const openGoogleMaps = () => {
    if (is_online && lat && lon) {
      window.open(`https://www.google.com/maps?q=${lat},${lon}`, '_blank')
    }
  }

  const isClickable = !showHealth && is_online && lat && lon

  return (
    <div
      onClick={isClickable ? openGoogleMaps : undefined}
      className={`rounded-xl shadow-lg overflow-hidden transition-all duration-300 ${
        showHealth
          ? (healthStatus?.text === 'ALL OK'
              ? 'bg-white dark:bg-gray-800 border-2 border-green-400'
              : 'bg-white dark:bg-gray-800 border-2 border-red-400')
          : is_online
            ? 'bg-white dark:bg-gray-800 border-2 border-green-400 cursor-pointer hover:shadow-xl hover:scale-[1.02]'
            : 'bg-gray-100 dark:bg-gray-700 border-2 border-gray-300 dark:border-gray-600 opacity-75'
      }`}
    >
      {/* Header */}
      <div
        className={`px-4 py-3 ${
          showHealth
            ? (healthStatus?.text === 'ALL OK'
                ? 'bg-gradient-to-r from-green-500 to-green-600'
                : 'bg-gradient-to-r from-red-500 to-red-600')
            : is_online
              ? 'bg-gradient-to-r from-green-500 to-green-600'
              : 'bg-gradient-to-r from-gray-400 to-gray-500 dark:from-gray-600 dark:to-gray-700'
        }`}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">{name}</h2>
          <span
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              showHealth
                ? (healthStatus?.text === 'ALL OK'
                    ? 'bg-white text-green-600'
                    : 'bg-white text-red-600')
                : is_online
                  ? 'bg-white text-green-600'
                  : 'bg-gray-200 dark:bg-gray-500 text-gray-600 dark:text-gray-200'
            }`}
          >
            {showHealth ? healthStatus?.text : (is_online ? 'ONLINE' : 'OFFLINE')}
          </span>
        </div>
      </div>

      {/* Body */}
      {showHealth ? (
        <HealthChain simulator={simulator} />
      ) : (
        <div className="p-4 space-y-4">
          {/* Position Section */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                Latitude
              </label>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {is_online ? formatCoord(lat, true) : '---'}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                Longitude
              </label>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {is_online ? formatCoord(lon, false) : '---'}
              </p>
            </div>
          </div>

          {/* Flight Data Section */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3 text-center">
              <label className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide">
                Altitude
              </label>
              <p className="text-xl font-bold text-blue-900 dark:text-blue-100">
                {is_online ? altitude_ft.toLocaleString() : '---'}
              </p>
              <span className="text-xs text-blue-600 dark:text-blue-400">ft MSL</span>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-3 text-center">
              <label className="text-xs font-medium text-purple-600 dark:text-purple-400 uppercase tracking-wide">
                Airspeed
              </label>
              <p className="text-xl font-bold text-purple-900 dark:text-purple-100">
                {is_online ? speed_kts : '---'}
              </p>
              <span className="text-xs text-purple-600 dark:text-purple-400">kts</span>
            </div>
            <div className="bg-orange-50 dark:bg-orange-900/30 rounded-lg p-3 text-center">
              <label className="text-xs font-medium text-orange-600 dark:text-orange-400 uppercase tracking-wide">
                Heading
              </label>
              <p className="text-xl font-bold text-orange-900 dark:text-orange-100">
                {is_online ? formatHeading(heading) : '---'}
              </p>
            </div>
          </div>

          {/* Nearest Airport Section */}
          <div className="bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/30 dark:to-primary-800/30 rounded-lg p-3">
            <label className="text-xs font-medium text-primary-600 dark:text-primary-400 uppercase tracking-wide">
              Nearest Airport
            </label>
            {is_online && closest_airport ? (
              <div className="mt-1">
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold text-primary-900 dark:text-primary-100">
                    {closest_airport.icao}
                  </span>
                  <span className="text-lg font-semibold text-primary-700 dark:text-primary-300">
                    {airport_distance_nm} NM
                  </span>
                </div>
                <p className="text-sm text-primary-700 dark:text-primary-300 truncate">
                  {closest_airport.name}
                </p>
              </div>
            ) : (
              <p className="text-lg font-semibold text-gray-400 dark:text-gray-500 mt-1">---</p>
            )}
          </div>

          {/* Packets Counter */}
          <div className="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500 pt-2 border-t border-gray-100 dark:border-gray-700">
            <span>Port: {simulator.port}</span>
            <span>Packets: {packet_count.toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default SimulatorCard
