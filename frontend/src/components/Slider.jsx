// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// Slider.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useState, useEffect } from 'react'
import { Minus, Plus } from 'lucide-react'

export default function Slider({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  unit = '',
  disabled = false
}) {
  // Local state for text input to allow typing without immediate clamping
  const [inputValue, setInputValue] = useState(String(value))
  const [isEditing, setIsEditing] = useState(false)

  // Sync local state when external value changes (but not while editing)
  useEffect(() => {
    if (!isEditing) {
      setInputValue(String(value))
    }
  }, [value, isEditing])

  const increment = () => onChange(Math.min(max, Math.round(value + step)))
  const decrement = () => onChange(Math.max(min, Math.round(value - step)))

  const commitValue = () => {
    const parsed = parseFloat(inputValue)
    if (!isNaN(parsed)) {
      const clamped = Math.max(min, Math.min(max, Math.round(parsed)))
      onChange(clamped)
      setInputValue(String(clamped))
    } else {
      // Reset to current value if invalid
      setInputValue(String(value))
    }
    setIsEditing(false)
  }

  return (
    <div className={disabled ? 'opacity-50' : ''}>
      <div className="flex items-center justify-between mb-2">
        <label className="label mb-0">{label}</label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={inputValue}
            onChange={(e) => {
              setIsEditing(true)
              setInputValue(e.target.value)
            }}
            onBlur={commitValue}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                commitValue()
                e.target.blur()
              }
            }}
            disabled={disabled}
            min={min}
            max={max}
            step={step}
            className="input w-24 text-center"
          />
          <span className="text-gray-500 dark:text-gray-400 text-sm w-12">{unit}</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={decrement}
          disabled={disabled || value <= min}
          className="p-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
        >
          <Minus className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        </button>

        <input
          type="range"
          value={value}
          onChange={(e) => onChange(Math.round(parseFloat(e.target.value)))}
          disabled={disabled}
          min={min}
          max={max}
          step={step}
          className="flex-1"
        />

        <button
          onClick={increment}
          disabled={disabled || value >= max}
          className="p-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
        >
          <Plus className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        </button>
      </div>
    </div>
  )
}
