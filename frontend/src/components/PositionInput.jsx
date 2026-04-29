// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// PositionInput.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useState, useEffect, useRef } from 'react'
import { MapPin, Search, Plane } from 'lucide-react'
import { api } from '../api/client'

export default function PositionInput({ lat, lon, airportIcao, onChange, disabled }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedAirport, setSelectedAirport] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef(null)
  const inputRef = useRef(null)

  // Load airport info if airportIcao is provided (synced from server)
  useEffect(() => {
    if (airportIcao && !selectedAirport) {
      api.lookupAirport(airportIcao).then(response => {
        if (response?.airport) {
          setSelectedAirport(response.airport)
          setQuery(response.airport.icao)
        }
      }).catch(err => {
        console.error('Failed to lookup airport:', err)
      })
    }
  }, [airportIcao, selectedAirport])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Search airports as user types
  useEffect(() => {
    if (query.length < 1) {
      setResults([])
      return
    }

    const searchTimer = setTimeout(async () => {
      setIsSearching(true)
      try {
        const response = await api.searchAirports(query, 10)
        setResults(response.airports || [])
        setShowDropdown(true)
      } catch (err) {
        console.error('Airport search error:', err)
        setResults([])
      } finally {
        setIsSearching(false)
      }
    }, 200)

    return () => clearTimeout(searchTimer)
  }, [query])

  const handleSelectAirport = (airport) => {
    setSelectedAirport(airport)
    setQuery(airport.icao)
    setShowDropdown(false)
    onChange({
      lat: airport.lat,
      lon: airport.lon,
      altitude_ft: airport.elevation_ft,
      airport_icao: airport.icao,
    })
  }

  const handleInputChange = (e) => {
    const value = e.target.value.toUpperCase()
    setQuery(value)
    if (value !== selectedAirport?.icao) {
      setSelectedAirport(null)
    }
  }

  const handleInputFocus = () => {
    if (results.length > 0) {
      setShowDropdown(true)
    }
  }

  return (
    <div className={`card ${disabled ? 'opacity-50' : ''}`}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
        <MapPin className="w-5 h-5 text-blue-500" />
        Position
      </h2>

      <div className="relative" ref={dropdownRef}>
        <label className="label">Airport (ICAO Code)</label>
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            disabled={disabled}
            placeholder="Enter ICAO code (e.g., KCRQ, KLAX)"
            className="input pr-10"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
            {isSearching ? (
              <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
          </div>
        </div>

        {/* Dropdown results */}
        {showDropdown && results.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {results.map((airport) => (
              <button
                key={airport.icao}
                onClick={() => handleSelectAirport(airport)}
                className="w-full px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 border-b border-gray-100 dark:border-gray-700 last:border-0"
              >
                <Plane className="w-4 h-4 text-blue-500 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="font-medium text-gray-900 dark:text-white">
                    {airport.icao}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                    {airport.name}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* No results message */}
        {showDropdown && query.length >= 1 && results.length === 0 && !isSearching && (
          <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg p-3 text-center text-gray-500 dark:text-gray-400">
            No airports found
          </div>
        )}
      </div>

      {/* Selected airport info */}
      {selectedAirport && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
            <Plane className="w-4 h-4" />
            <span className="font-medium">{selectedAirport.icao}</span>
          </div>
          <div className="text-sm text-blue-600 dark:text-blue-400 mt-1">
            {selectedAirport.name}
          </div>
          <div className="text-xs text-blue-500 dark:text-blue-500 mt-1">
            Elevation: {(selectedAirport.elevation_ft ?? 0).toLocaleString()} ft
          </div>
        </div>
      )}
    </div>
  )
}
