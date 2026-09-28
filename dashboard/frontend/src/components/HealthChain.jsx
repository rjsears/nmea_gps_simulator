function HealthChain({ simulator }) {
  const { name, emulator_online, sim_reachable, is_online, gps_system, switch_ip, switch_reachable } = simulator

  // Smart gating: if GPS data is flowing, everything is implicitly OK
  const allImplicitlyOk = is_online
  const switchConfigured = switch_reachable !== null && switch_reachable !== undefined

  const dashboardOk = true // Always true if we're rendering
  const emulatorOk = allImplicitlyOk || emulator_online
  // Second smart gate: if the emulator can still ping the simulator THROUGH the switch,
  // the switch is forwarding traffic even if its management IP does not answer.
  const switchOk = allImplicitlyOk || !switchConfigured || switch_reachable || sim_reachable
  const simulatorOk = allImplicitlyOk || (emulatorOk && switchOk && sim_reachable)
  const gpsDataOk = is_online

  // Find first failure point (only if not implicitly OK)
  let failurePoint = null
  let failureMessage = ''
  if (!allImplicitlyOk) {
    if (!emulator_online) {
      failurePoint = 'emulator'
      failureMessage = 'Is the emulator container running?'
    } else if (switchConfigured && !switch_reachable && !sim_reachable) {
      failurePoint = 'switch'
      failureMessage = `Switch for ${name} (${switch_ip}) is not responding. Check switch power and uplink.`
    } else if (!sim_reachable) {
      failurePoint = 'simulator'
      failureMessage = 'Is the simulator powered on? If yes, possible network issue.'
    } else if (!is_online) {
      failurePoint = 'gps'
      if (gps_system) {
        failureMessage = `Not receiving GPS data. Start or Restart GPSConnect application on ${gps_system}.`
      } else {
        failureMessage = 'Not receiving GPS data. Start or Restart the GPSConnect application on the simulator.'
      }
    }
  }

  const allOk = !failurePoint

  const NodeBox = ({ icon, label, isFailed, isAfterFailure }) => {
    let bgColor, borderColor, textColor
    if (isFailed) {
      // Failed: gray interior like after-failure, but bright red border
      bgColor = 'bg-gray-100 dark:bg-gray-700'
      borderColor = 'border-red-500'
      textColor = 'text-red-600 dark:text-red-400'
    } else if (isAfterFailure) {
      bgColor = 'bg-gray-100 dark:bg-gray-700'
      borderColor = 'border-gray-300 dark:border-gray-600'
      textColor = 'text-gray-400 dark:text-gray-500'
    } else {
      bgColor = 'bg-green-100 dark:bg-green-900/30'
      borderColor = 'border-green-500'
      textColor = 'text-gray-700 dark:text-gray-300'
    }

    return (
      <div className="flex flex-col items-center">
        <div className={`w-16 h-16 ${bgColor} border-2 ${borderColor} rounded-lg flex items-center justify-center text-3xl ${isFailed ? 'ring-4 ring-red-500/30 shadow-[0_0_14px_4px_rgba(239,68,68,0.55)]' : ''}`}>
          <span className={isAfterFailure ? 'grayscale opacity-50' : ''}>{icon}</span>
        </div>
        <div className={`text-sm mt-1 font-medium ${textColor}`}>
          {label}
        </div>
      </div>
    )
  }

  const Connector = ({ ok, isAfterFailure }) => {
    let bgColor = 'bg-green-500'
    if (isAfterFailure) {
      bgColor = 'bg-gray-300 dark:bg-gray-600'
    } else if (!ok) {
      bgColor = 'bg-red-500'
    }
    // mt-8 positions line at center of h-16 box, h-6 matches text-sm label height plus mt-1 below
    return (
      <div className="flex flex-col">
        <div className={`h-0.5 w-5 mt-8 ${bgColor}`} />
        <div className="h-6" />
      </div>
    )
  }

  const afterEmulator = failurePoint === 'emulator'
  const afterSwitch = failurePoint === 'emulator' || failurePoint === 'switch'
  const afterSimulator = afterSwitch || failurePoint === 'simulator'

  return (
    <div className="px-2 py-4">
      <div className="flex items-start justify-between">
        <NodeBox icon="📊" label="Dashboard" isFailed={false} isAfterFailure={false} />
        <Connector ok={emulatorOk} isAfterFailure={false} />
        <NodeBox icon="🖥️" label="Emulator" isFailed={failurePoint === 'emulator'} isAfterFailure={false} />
        <Connector ok={switchOk} isAfterFailure={afterEmulator} />
        <NodeBox icon="🔀" label="Switch" isFailed={failurePoint === 'switch'} isAfterFailure={afterEmulator} />
        <Connector ok={simulatorOk} isAfterFailure={afterSwitch} />
        <NodeBox icon="✈️" label="Simulator" isFailed={failurePoint === 'simulator'} isAfterFailure={afterSwitch} />
        <Connector ok={gpsDataOk} isAfterFailure={afterSimulator} />
        <NodeBox icon="🛰️" label="GPS Data" isFailed={failurePoint === 'gps'} isAfterFailure={afterSimulator} />
      </div>

      {allOk ? (
        <div className="mt-4 p-3 bg-green-100 dark:bg-green-900/30 rounded-lg text-sm text-green-800 dark:text-green-200 text-center font-medium">
          All systems operational
        </div>
      ) : (
        <div className="mt-4 p-3 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg text-sm text-yellow-800 dark:text-yellow-200">
          <strong>Check:</strong> {failureMessage}
        </div>
      )}
    </div>
  )
}

export default HealthChain
