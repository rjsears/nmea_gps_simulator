// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// StandaloneConfig.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 28th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useState, useEffect } from 'react'
import { Usb, Plane, RefreshCw, Settings } from 'lucide-react'
import { api } from '../api/client'

const BAUD_RATES = [
  { value: 1200, label: '1200 - Legacy modems' },
  { value: 2400, label: '2400 - Low-speed printers' },
  { value: 4800, label: '4800 - GPS modules' },
  { value: 9600, label: '9600 - Common default' },
  { value: 19200, label: '19200 - Industrial/PLC' },
  { value: 38400, label: '38400 - Instrumentation' },
  { value: 57600, label: '57600 - Higher speed' },
  { value: 115200, label: '115200 - USB-serial (default)' },
]

export default function StandaloneConfig({
  modes,
  network,
  serial,
  onModeChange,
  onNetworkChange,
  onSerialSelect,
  onBaudChange,
  disabled
}) {
  const [ports, setPorts] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchPorts = async () => {
    setLoading(true)
    try {
      const data = await api.listDevices()
      setPorts(data.devices || [])
    } catch (err) {
      console.error('Failed to fetch ports:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPorts()
  }, [])

  const handleModeChange = (field, value) => {
    onModeChange({ ...modes, [field]: value })
  }

  const handleNetworkChange = (field, value) => {
    onNetworkChange({ ...network, [field]: value })
  }

  return (
    <div className={`card ${disabled ? 'opacity-50' : ''}`}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
        <Settings className="w-5 h-5 text-blue-500" />
        Output Settings
      </h2>

      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Select at least one output method:
      </p>

      <div className="space-y-4">
        {/* USB Output */}
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="standalone-usb"
                checked={modes.usb_output || false}
                onChange={(e) => handleModeChange('usb_output', e.target.checked)}
                disabled={disabled}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <label htmlFor="standalone-usb" className="font-medium text-gray-900 dark:text-white cursor-pointer flex items-center gap-2">
                <Usb className="w-4 h-4 text-green-500" />
                USB Serial Output
              </label>
            </div>
            {modes.usb_output && (
              <button
                onClick={fetchPorts}
                disabled={disabled || loading}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Refresh ports"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>

          {modes.usb_output && (
            <div className="ml-7 space-y-3">
              <div>
                <label className="label text-sm">Device</label>
                <select
                  value={serial.device || ''}
                  onChange={(e) => onSerialSelect(e.target.value)}
                  disabled={disabled}
                  className="select"
                >
                  <option value="">Select device...</option>
                  {ports.map((d) => (
                    <option key={d.device} value={d.device}>
                      {d.device} {d.description && `- ${d.description}`}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label text-sm">Baud Rate</label>
                <select
                  value={serial.baudrate || 115200}
                  onChange={(e) => onBaudChange(parseInt(e.target.value))}
                  disabled={disabled}
                  className="select"
                >
                  {BAUD_RATES.map((rate) => (
                    <option key={rate.value} value={rate.value}>{rate.label}</option>
                  ))}
                </select>
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Format: 8N1 (8 data bits, no parity, 1 stop bit)
              </div>
            </div>
          )}
        </div>

        {/* EFB Output */}
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-3">
          <div className="flex items-start gap-3">
            <input
              type="checkbox"
              id="standalone-efb"
              checked={network.efb_enabled || false}
              onChange={(e) => handleNetworkChange('efb_enabled', e.target.checked)}
              disabled={disabled}
              className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <div className="flex-1">
              <label htmlFor="standalone-efb" className="font-medium text-gray-900 dark:text-white cursor-pointer flex items-center gap-2">
                <Plane className="w-4 h-4 text-blue-500" />
                EFB Output (Port 49002)
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Send XGPS data to ForeFlight / Garmin Pilot
              </p>
            </div>
          </div>

          {network.efb_enabled && (
            <div className="ml-7 space-y-3 pt-2 border-t border-gray-200 dark:border-gray-700">
              {/* Broadcast Checkbox */}
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="standalone-broadcast"
                  checked={network.foreflight_broadcast || false}
                  onChange={(e) => handleNetworkChange('foreflight_broadcast', e.target.checked)}
                  disabled={disabled}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="standalone-broadcast" className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                  Broadcast
                </label>
              </div>

              {/* Garmin Pilot/ForeFlight (IP Address) */}
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="standalone-efb-ip"
                    checked={network.efb_ip_enabled || false}
                    onChange={(e) => handleNetworkChange('efb_ip_enabled', e.target.checked)}
                    disabled={disabled}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="standalone-efb-ip" className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                    Garmin Pilot/ForeFlight (IP Address)
                  </label>
                </div>
                {network.efb_ip_enabled && (
                  <div className="ml-7 space-y-1">
                    <input
                      type="text"
                      value={network.efb_target_ips || ''}
                      onChange={(e) => handleNetworkChange('efb_target_ips', e.target.value)}
                      disabled={disabled}
                      placeholder="e.g., 10.200.50.3, 10.200.50.10-10.200.50.20"
                      className="input"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Comma-separated IPs or ranges (e.g., 10.0.0.5, 10.0.0.10-10.0.0.20)
                    </p>
                  </div>
                )}
              </div>

              {/* Simulator Name */}
              <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                <label className="label text-sm">Simulator Name <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  value={network.foreflight_sim_name ?? ''}
                  onChange={(e) => handleNetworkChange('foreflight_sim_name', e.target.value)}
                  disabled={disabled}
                  placeholder="e.g., CL350, ULTRA"
                  className="input"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
