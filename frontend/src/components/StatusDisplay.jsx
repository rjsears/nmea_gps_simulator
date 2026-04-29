// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// StatusDisplay.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { Activity, Wifi, WifiOff, Usb, MapPin } from 'lucide-react'

export default function StatusDisplay({ status, selectedDevice }) {
  if (!status) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-blue-500" />
          Status
        </h2>
        <p className="text-gray-500 dark:text-gray-400">Loading status...</p>
      </div>
    )
  }

  const isRunning = status.gps?.is_running || false

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-blue-500" />
        Status
      </h2>

      <div className="space-y-3">
        {/* Emulator Status */}
        <div className="flex items-center justify-between">
          <span className="text-gray-500 dark:text-gray-400">Emulator</span>
          <div className="flex items-center gap-2">
            <span className={`status-indicator ${isRunning ? 'connected' : 'disconnected'}`}></span>
            <span className={isRunning ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              {isRunning ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>

        {/* Serial Status - use selectedDevice prop */}
        <div className="flex items-center justify-between">
          <span className="text-gray-500 dark:text-gray-400 flex items-center gap-2">
            <Usb className="w-4 h-4" />
            Serial
          </span>
          <div className="flex items-center gap-2">
            <span className={`status-indicator ${selectedDevice ? 'connected' : 'disconnected'}`}></span>
            <span className={selectedDevice ? 'text-green-600 dark:text-green-400 text-sm' : 'text-gray-500 dark:text-gray-400 text-sm'}>
              {selectedDevice || 'Not selected'}
            </span>
          </div>
        </div>

        {/* Network Status (if sender or receiver mode) */}
        {(status.modes?.sender || status.modes?.receiver) && (
          <div className="flex items-center justify-between">
            <span className="text-gray-500 dark:text-gray-400 flex items-center gap-2">
              {status.network_connected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              Network
            </span>
            <div className="flex items-center gap-2">
              <span className={`status-indicator ${status.network_connected ? 'connected' : 'disconnected'}`}></span>
              <span className="text-gray-600 dark:text-gray-300 text-sm">
                {status.network?.protocol?.toUpperCase()} : {status.network?.port}
              </span>
            </div>
          </div>
        )}

        <hr className="border-gray-200 dark:border-gray-700" />

        {/* Current Position */}
        <div className="flex items-center justify-between">
          <span className="text-gray-500 dark:text-gray-400 flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Position
          </span>
          <span className="font-mono text-sm text-gray-900 dark:text-white">
            {(status.gps?.lat ?? 0).toFixed(4)}, {(status.gps?.lon ?? 0).toFixed(4)}
          </span>
        </div>

        {/* Altitude */}
        <div className="flex items-center justify-between">
          <span className="text-gray-500 dark:text-gray-400">Altitude</span>
          <span className="font-mono text-gray-900 dark:text-white">{(status.gps?.altitude_ft ?? 0).toLocaleString()} ft</span>
        </div>

        {/* Speed */}
        <div className="flex items-center justify-between">
          <span className="text-gray-500 dark:text-gray-400">Airspeed</span>
          <span className="font-mono text-gray-900 dark:text-white">{status.gps?.speed_kts ?? 0} kts</span>
        </div>

        {/* Heading */}
        <div className="flex items-center justify-between">
          <span className="text-gray-500 dark:text-gray-400">Heading</span>
          <span className="font-mono text-gray-900 dark:text-white">{status.gps?.heading ?? 0} deg</span>
        </div>
      </div>
    </div>
  )
}
