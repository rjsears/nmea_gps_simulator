// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// SerialSelector.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useState, useEffect } from 'react'
import { Usb, RefreshCw } from 'lucide-react'
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

export default function SerialSelector({ device, baudrate = 115200, onSelect, onBaudChange, disabled }) {
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

  return (
    <div className={`card ${disabled ? 'opacity-50' : ''}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Usb className="w-5 h-5 text-green-500" />
          Serial Port
        </h2>

        <button
          onClick={fetchPorts}
          disabled={disabled || loading}
          className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          title="Refresh ports"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div>
        <label className="label">Device</label>
        <select
          value={device || ''}
          onChange={(e) => onSelect(e.target.value || null)}
          disabled={disabled}
          className="select"
        >
          <option value="">Select device...</option>
          {ports.map((port) => (
            <option key={port.device} value={port.device}>
              {port.device} {port.description && `- ${port.description}`}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-3">
        <label className="label">Baud Rate</label>
        <select
          value={baudrate}
          onChange={(e) => onBaudChange(parseInt(e.target.value, 10))}
          disabled={disabled}
          className="select"
        >
          {BAUD_RATES.map((rate) => (
            <option key={rate.value} value={rate.value}>
              {rate.label}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-3 text-sm text-gray-500 dark:text-gray-400">
        Format: 8N1 (8 data bits, no parity, 1 stop bit)
      </div>
    </div>
  )
}
