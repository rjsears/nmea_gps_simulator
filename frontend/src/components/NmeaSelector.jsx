// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// NmeaSelector.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { FileText, Lock } from 'lucide-react'

const NMEA_SENTENCES = [
  { id: 'gpgga', name: 'GPGGA', description: 'Fix Data', required: true },
  { id: 'gprmc', name: 'GPRMC', description: 'Recommended Min', required: true },
  { id: 'gpgll', name: 'GPGLL', description: 'Position', required: false },
  { id: 'gpvtg', name: 'GPVTG', description: 'Track/Speed', required: false },
  { id: 'gpgsa', name: 'GPGSA', description: 'DOP & Satellites', required: false },
  { id: 'gpgsv', name: 'GPGSV', description: 'Sats in View', required: false },
  { id: 'gpzda', name: 'GPZDA', description: 'Time & Date', required: false },
  { id: 'gphdt', name: 'GPHDT', description: 'True Heading', required: false },
]

export default function NmeaSelector({ config, onChange, disabled }) {
  const handleToggle = (id) => {
    const sentence = NMEA_SENTENCES.find(s => s.id === id)
    if (sentence?.required) return // Don't allow toggling required sentences

    onChange({
      ...config,
      [id]: !config[id],
    })
  }

  return (
    <div className={`card ${disabled ? 'opacity-50' : ''}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-500" />
          NMEA Sentences
        </h2>
      </div>

      <div className="space-y-2">
        {NMEA_SENTENCES.map((sentence) => (
          <label
            key={sentence.id}
            className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors
              ${config[sentence.id] ? 'bg-blue-50 dark:bg-blue-900/30' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}
              ${sentence.required ? 'cursor-not-allowed' : ''}
            `}
          >
            <input
              type="checkbox"
              checked={config[sentence.id] || false}
              onChange={() => handleToggle(sentence.id)}
              disabled={disabled || sentence.required}
              className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-blue-600 focus:ring-blue-500 flex-shrink-0"
            />
            <span className="font-mono text-sm text-gray-900 dark:text-white w-16 flex-shrink-0">{sentence.name}</span>
            {sentence.required && (
              <Lock className="w-3 h-3 text-gray-400 flex-shrink-0" title="Required" />
            )}
            <span className="text-gray-500 dark:text-gray-400 text-sm truncate">{sentence.description}</span>
          </label>
        ))}
      </div>

      <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
        GPGGA and GPRMC are required and always enabled.
      </p>
    </div>
  )
}
