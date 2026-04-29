// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// useStatus.js
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import { useWebSocket } from './useWebSocket'

export function useStatus() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const handleWebSocketMessage = useCallback((data) => {
    if (data.type === 'status') {
      setStatus(data.payload)
    }
  }, [])

  const { connected: wsConnected } = useWebSocket(handleWebSocketMessage)

  const fetchStatus = useCallback(async () => {
    try {
      const data = await api.getStatus()
      setStatus(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()

    // Poll status every second when running
    const interval = setInterval(() => {
      fetchStatus()
    }, 1000)

    return () => clearInterval(interval)
  }, [fetchStatus])

  return { status, loading, error, refresh: fetchStatus, wsConnected }
}
