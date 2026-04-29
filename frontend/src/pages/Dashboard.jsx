// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// Dashboard.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useState, useEffect, useCallback } from 'react'
import Layout from '../components/Layout'
import ModeSelector from '../components/ModeSelector'
import PositionInput from '../components/PositionInput'
import NavigationControls from '../components/NavigationControls'
import SerialSelector from '../components/SerialSelector'
import NmeaSelector from '../components/NmeaSelector'
import NetworkConfig from '../components/NetworkConfig'
import RebroadcasterConfig from '../components/RebroadcasterConfig'
import StandaloneConfig from '../components/StandaloneConfig'
import StatusDisplay from '../components/StatusDisplay'
import StartStopButton from '../components/StartStopButton'
import OutputViewer from '../components/OutputViewer'
import { api } from '../api/client'
import { useStatus } from '../hooks/useStatus'
import { AlertCircle, Loader2 } from 'lucide-react'

// Helper to extract error message from various error types
function getErrorMessage(err) {
  if (typeof err === 'string') return err
  if (err?.message) return err.message
  if (err?.detail) return err.detail
  if (err?.error) return err.error
  try {
    return JSON.stringify(err)
  } catch {
    return 'An unknown error occurred'
  }
}

export default function Dashboard() {
  const { status, loading, error, refresh } = useStatus()
  const [localState, setLocalState] = useState(null)
  const [apiError, setApiError] = useState(null)
  const [airportSelected, setAirportSelected] = useState(false)

  // Initialize local state from server status
  useEffect(() => {
    if (status && !localState) {
      const gps = status.gps || { lat: 0, lon: 0, altitude_ft: 0, speed_kts: 0, heading: 360, is_running: false }
      // Ensure target values default to current values if not set
      const gpsWithTargets = {
        ...gps,
        target_altitude_ft: gps.target_altitude_ft ?? gps.altitude_ft,
        target_speed_kts: gps.target_speed_kts ?? gps.speed_kts,
        target_heading: gps.target_heading ?? gps.heading,
      }
      setLocalState({
        modes: status.modes || { standalone: false, sender: false, receiver: false, usb_output: false },
        gps: gpsWithTargets,
        network: status.network || { protocol: 'udp', target_ip: '', port: 12000 },
        serial: status.serial || { device: null, baudrate: 115200 },
        nmea: status.nmea || { gpgga: true, gprmc: true, gpgll: false, gpgsa: false, gpgsv: false, gphdt: false, gpvtg: false, gpzda: false },
      })
      // If emulator is already running or airport was previously selected, mark airport as selected
      // This handles the case where a new browser connects to a running emulator
      if (gps.is_running || gps.airport_icao) {
        setAirportSelected(true)
      }
    }
  }, [status, localState])

  // Update local state from real-time status
  // Sync only is_running and GPS target values from server
  // Don't sync config (modes, network, serial, nmea) - user's local state is authoritative
  // This prevents race conditions where status polling overwrites user input before API completes
  useEffect(() => {
    if (status && localState) {
      setLocalState(prev => ({
        ...prev,
        // Don't sync config from server - user's local state is authoritative
        // Only sync is_running and target values
        gps: {
          ...prev.gps,
          is_running: status.gps?.is_running ?? prev.gps.is_running,
          // Sync target values so other browsers see slider changes
          target_altitude_ft: status.gps?.target_altitude_ft ?? prev.gps.target_altitude_ft,
          target_speed_kts: status.gps?.target_speed_kts ?? prev.gps.target_speed_kts,
          target_heading: status.gps?.target_heading ?? prev.gps.target_heading,
          // Sync airport selection for multi-browser support
          airport_icao: status.gps?.airport_icao ?? prev.gps.airport_icao,
        },
      }))
      // Update airportSelected if emulator started externally or airport set from another browser
      if ((status.gps?.is_running && !localState?.gps?.is_running) || status.gps?.airport_icao) {
        setAirportSelected(true)
      }
    }
  }, [status])

  const isRunning = localState?.gps?.is_running || false

  const handleModeChange = useCallback(async (modes) => {
    setLocalState(prev => ({ ...prev, modes }))
    try {
      await api.updateModes(modes)
      setApiError(null)
    } catch (err) {
      console.error('Failed to update modes:', err)
      setApiError(getErrorMessage(err))
    }
  }, [])

  const handlePositionChange = useCallback(async (update) => {
    // Mark airport as selected if lat/lon are being set (from airport picker)
    if (update.lat !== undefined && update.lon !== undefined) {
      setAirportSelected(true)
    }
    // Build updates including target values for altitude/speed/heading
    const gpsUpdate = { ...update }
    if (update.altitude_ft !== undefined) {
      gpsUpdate.target_altitude_ft = update.altitude_ft
    }
    if (update.speed_kts !== undefined) {
      gpsUpdate.target_speed_kts = update.speed_kts
    }
    if (update.heading !== undefined) {
      gpsUpdate.target_heading = update.heading
    }
    setLocalState(prev => ({
      ...prev,
      gps: { ...prev.gps, ...gpsUpdate },
    }))
    try {
      await api.updatePosition(update)
      setApiError(null)
    } catch (err) {
      console.error('Failed to update position:', err)
      setApiError(getErrorMessage(err))
    }
  }, [])

  const handleNetworkChange = useCallback(async (network) => {
    setLocalState(prev => ({ ...prev, network }))
    try {
      await api.updateNetwork(network)
      setApiError(null)
    } catch (err) {
      console.error('Failed to update network:', err)
      setApiError(getErrorMessage(err))
    }
  }, [])

  const handleNmeaChange = useCallback(async (nmea) => {
    setLocalState(prev => ({ ...prev, nmea }))
    try {
      await api.updateNmea(nmea)
      setApiError(null)
    } catch (err) {
      console.error('Failed to update NMEA:', err)
      setApiError(getErrorMessage(err))
    }
  }, [])

  const handleSerialSelect = useCallback(async (device) => {
    setLocalState(prev => ({
      ...prev,
      serial: { ...prev.serial, device },
    }))
    try {
      await api.selectDevice(device)
      setApiError(null)
    } catch (err) {
      console.error('Failed to select device:', err)
      setApiError(getErrorMessage(err))
    }
  }, [])

  const handleBaudChange = useCallback(async (baudrate) => {
    setLocalState(prev => ({
      ...prev,
      serial: { ...prev.serial, baudrate },
    }))
    try {
      await api.updateSerial({ ...localState.serial, baudrate })
      setApiError(null)
    } catch (err) {
      console.error('Failed to update baud rate:', err)
      setApiError(getErrorMessage(err))
    }
  }, [localState?.serial])

  const handleStart = useCallback(async () => {
    try {
      await api.start()
      setApiError(null)
      refresh()
    } catch (err) {
      console.error('Failed to start:', err)
      setApiError(getErrorMessage(err))
    }
  }, [refresh])

  const handleStop = useCallback(async () => {
    try {
      await api.stop()
      setApiError(null)
      refresh()
    } catch (err) {
      console.error('Failed to stop:', err)
      setApiError(getErrorMessage(err))
    }
  }, [refresh])

  // Validation: can start?
  const hasModeSelected = localState && (
    localState.modes.standalone ||
    localState.modes.sender ||
    localState.modes.receiver ||
    localState.modes.rebroadcaster
  )
  // Receiver and rebroadcaster don't need airport (they receive data)
  const needsAirport = localState && !localState.modes.receiver && !localState.modes.rebroadcaster && !airportSelected

  // EFB configuration
  const efbMasterEnabled = localState?.network?.efb_enabled || false
  const foreflightBroadcast = localState?.network?.foreflight_broadcast || false
  const efbIpEnabled = localState?.network?.efb_ip_enabled || false
  const efbHasOutput = efbMasterEnabled && (foreflightBroadcast || efbIpEnabled)
  const efbSimName = localState?.network?.foreflight_sim_name?.trim()
  const efbTargetIps = localState?.network?.efb_target_ips?.trim()

  // Standalone mode: need at least one output (USB or EFB)
  const standaloneUsbEnabled = localState?.modes?.usb_output || false
  const hasStandaloneOutput = standaloneUsbEnabled || efbHasOutput
  const needsStandaloneConfig = localState && localState.modes.standalone && !hasStandaloneOutput

  // Standalone USB requires serial device (only if USB is enabled)
  const needsStandaloneSerial = localState && localState.modes.standalone && standaloneUsbEnabled && !localState.serial.device

  // USB output (receiver mode without rebroadcaster) requires serial device
  const needsSerial = localState && !localState.modes.standalone && !localState.modes.sender && !localState.modes.rebroadcaster && localState.modes.usb_output && !localState.serial.device

  // For sender mode: need at least one output enabled (NMEA with IP, EFB, or USB)
  const nmeaEnabled = localState?.network?.nmea_output === true
  const hasNmeaWithIp = nmeaEnabled && localState?.network?.target_ip
  const senderUsbEnabled = localState?.modes?.sender && localState?.modes?.usb_output
  const hasSenderOutput = hasNmeaWithIp || efbHasOutput || senderUsbEnabled
  const needsSenderConfig = localState && localState.modes.sender && !hasSenderOutput

  // Sender USB requires serial device
  const needsSenderSerial = localState && localState.modes.sender && senderUsbEnabled && !localState.serial.device

  // EFB requires a simulator name when enabled with at least one output
  // Only check when EFB is actually being used (efbHasOutput is true)
  const needsSimName = efbHasOutput && !efbSimName

  // EFB IP targets requires at least one IP address
  const needsEfbTargetIps = efbMasterEnabled && efbIpEnabled && !efbTargetIps

  // EFB enabled but no sub-option selected - only check when EFB master is enabled
  const needsEfbSubOption = efbMasterEnabled && !foreflightBroadcast && !efbIpEnabled

  // Rebroadcaster mode: need at least one output enabled (USB, EFB, or UDP retransmit)
  const rebroadcastUsb = localState?.network?.rebroadcast_usb || false
  const rebroadcastUdp = localState?.network?.rebroadcast_udp || false
  const rebroadcastUdpIp = localState?.network?.rebroadcast_udp_ip?.trim()
  const hasRebroadcastOutput = rebroadcastUsb || efbHasOutput || (rebroadcastUdp && rebroadcastUdpIp)
  const needsRebroadcastConfig = localState && localState.modes.rebroadcaster && !hasRebroadcastOutput

  // Rebroadcaster USB requires serial device
  const needsRebroadcastSerial = localState && localState.modes.rebroadcaster && rebroadcastUsb && !localState.serial.device

  // Rebroadcaster UDP requires IP
  const needsRebroadcastUdpIp = localState && localState.modes.rebroadcaster && rebroadcastUdp && !rebroadcastUdpIp

  const canStart = hasModeSelected && !needsAirport && !needsSerial && !needsStandaloneConfig && !needsStandaloneSerial && !needsSenderConfig && !needsSenderSerial && !needsSimName && !needsEfbTargetIps && !needsEfbSubOption && !needsRebroadcastConfig && !needsRebroadcastSerial && !needsRebroadcastUdpIp

  // Debug logging
  console.log('Validation:', { hasModeSelected, needsAirport, needsSerial, needsStandaloneConfig, needsStandaloneSerial, needsSenderConfig, needsSenderSerial, needsSimName, needsEfbTargetIps, needsEfbSubOption, needsRebroadcastConfig, canStart, airportSelected, modes: localState?.modes })

  // Determine why button is disabled
  const getDisabledReason = () => {
    if (!hasModeSelected) return 'Select an operating mode'
    if (needsAirport) return 'Select an airport'
    if (needsStandaloneConfig) return 'Select at least one output (USB or EFB)'
    if (needsStandaloneSerial) return 'Select a USB device'
    if (needsSerial) return 'Select a USB device'
    if (needsSenderConfig) {
      if (nmeaEnabled && !localState.network.target_ip) return 'Enter target IP address for NMEA output'
      return 'Enable at least one output (NMEA, EFB, or USB)'
    }
    if (needsSenderSerial) return 'Select a USB device'
    if (needsEfbSubOption) return 'Select Broadcast or Garmin Pilot/ForeFlight (IP Address)'
    if (needsSimName) return 'Enter a simulator name for EFB output'
    if (needsEfbTargetIps) return 'Enter IP address(es) for EFB output'
    if (needsRebroadcastConfig) return 'Select at least one rebroadcast output (USB, EFB, or UDP)'
    if (needsRebroadcastSerial) return 'Select a USB device for rebroadcast'
    if (needsRebroadcastUdpIp) return 'Enter target IP for UDP retransmit'
    return null
  }
  const disabledReason = getDisabledReason()

  // Loading state
  if (loading) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500 mb-4" />
          <div className="text-lg text-gray-600 dark:text-gray-400">Loading...</div>
        </div>
      </Layout>
    )
  }

  // Error state from initial fetch
  if (error) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 p-4 text-red-600 bg-red-50 dark:bg-red-900/30 dark:text-red-400 rounded-lg">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <div>
              <p className="font-medium">Error loading status</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  // Waiting for local state to be initialized
  if (!localState) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500 mb-4" />
          <div className="text-lg text-gray-600 dark:text-gray-400">Initializing...</div>
        </div>
      </Layout>
    )
  }

  const showStandalone = localState.modes.standalone
  const showSerial = !localState.modes.standalone && !localState.modes.rebroadcaster && !localState.modes.sender && localState.modes.usb_output
  const showNetwork = localState.modes.sender || localState.modes.receiver
  const showRebroadcaster = localState.modes.rebroadcaster

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Error Alert */}
        {apiError && (
          <div className="flex items-center gap-3 p-4 text-red-600 bg-red-50 dark:bg-red-900/30 dark:text-red-400 rounded-lg">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span>{apiError}</span>
            <button
              onClick={() => setApiError(null)}
              className="ml-auto text-red-400 hover:text-red-600"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left column - Mode, Serial, Network */}
          <div className="lg:col-span-4 space-y-6">
            <ModeSelector
              modes={localState.modes}
              onChange={handleModeChange}
              disabled={isRunning}
            />

            {showStandalone && (
              <StandaloneConfig
                modes={localState.modes}
                network={localState.network}
                serial={localState.serial}
                onModeChange={handleModeChange}
                onNetworkChange={handleNetworkChange}
                onSerialSelect={handleSerialSelect}
                onBaudChange={handleBaudChange}
                disabled={isRunning}
              />
            )}

            {showNetwork && (
              <NetworkConfig
                config={localState.network}
                modes={localState.modes}
                serial={localState.serial}
                onChange={handleNetworkChange}
                onModeChange={handleModeChange}
                onSerialSelect={handleSerialSelect}
                onBaudChange={handleBaudChange}
                isSender={localState.modes.sender}
                isReceiver={localState.modes.receiver}
                disabled={isRunning}
              />
            )}

            {showSerial && (
              <SerialSelector
                device={localState.serial.device}
                baudrate={localState.serial.baudrate}
                onSelect={handleSerialSelect}
                onBaudChange={handleBaudChange}
                disabled={isRunning}
              />
            )}

            {showRebroadcaster && (
              <RebroadcasterConfig
                config={localState.network}
                serialDevice={localState.serial.device}
                serialBaudrate={localState.serial.baudrate}
                onConfigChange={handleNetworkChange}
                onSerialSelect={handleSerialSelect}
                onBaudChange={handleBaudChange}
                disabled={isRunning}
              />
            )}
          </div>

          {/* Center column - Position, Navigation, Start/Stop */}
          <div className="lg:col-span-4 space-y-6">
            <PositionInput
              lat={localState.gps.lat}
              lon={localState.gps.lon}
              airportIcao={localState.gps.airport_icao}
              onChange={handlePositionChange}
              disabled={localState.modes.receiver}
            />

            <NavigationControls
              altitude={localState.gps.target_altitude_ft ?? localState.gps.altitude_ft}
              speed={localState.gps.target_speed_kts ?? localState.gps.speed_kts}
              heading={localState.gps.target_heading ?? localState.gps.heading}
              onChange={handlePositionChange}
              disabled={localState.modes.receiver}
            />

            <StartStopButton
              isRunning={isRunning}
              onStart={handleStart}
              onStop={handleStop}
              disabled={!isRunning && !canStart}
              disabledReason={disabledReason}
            />
          </div>

          {/* Right column - NMEA, Status */}
          <div className="lg:col-span-4 space-y-6">
            <NmeaSelector
              config={localState.nmea}
              onChange={handleNmeaChange}
              disabled={isRunning || localState.modes.receiver}
            />

            <StatusDisplay
              status={status}
              selectedDevice={localState.serial.device}
            />
          </div>
        </div>

        {/* Full-width NMEA Output at bottom */}
        <OutputViewer isRunning={isRunning} isReceiver={localState.modes.receiver} />
      </div>
    </Layout>
  )
}
