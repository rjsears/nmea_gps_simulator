function HealthChain({ simulator }) {
  const { emulator_online, sim_reachable, is_online } = simulator

  // Smart gating: if GPS data is flowing, everything is implicitly OK
  const allImplicitlyOk = is_online

  // Determine status of each node
  const dashboardOk = true // Always true if we're rendering
  const emulatorOk = allImplicitlyOk || emulator_online
  const simulatorOk = allImplicitlyOk || (emulatorOk && sim_reachable)
  const gpsDataOk = is_online

  // Find first failure point (only if not implicitly OK)
  let failurePoint = null
  let failureMessage = ''
  if (!allImplicitlyOk) {
    if (!emulator_online) {
      failurePoint = 'emulator'
      failureMessage = 'Is the emulator container running?'
    } else if (!sim_reachable) {
      failurePoint = 'simulator'
      failureMessage = 'Is the simulator powered on? If yes, possible network issue.'
    } else if (!is_online) {
      failurePoint = 'gps'
      failureMessage = 'GPS software on simulator may have crashed. Restart the GPS application.'
    }
  }

  const allOk = !failurePoint

  const NodeBox = ({ icon, label, status, isFailed, isAfterFailure }) => {
    let bgColor, borderColor, textColor
    if (isFailed) {
      bgColor = 'bg-red-100 dark:bg-red-900/30'
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
      <div className="text-center">
        <div className={`w-12 h-12 ${bgColor} border-2 ${borderColor} rounded-lg flex items-center justify-center text-2xl relative`}>
          {icon}
          {isFailed && (
            <span className="absolute inset-0 flex items-center justify-center text-4xl text-gray-500 dark:text-gray-400 font-thin z-10">
              ✕
            </span>
          )}
        </div>
        <div className={`text-xs mt-1 font-medium ${isFailed ? 'text-red-600 dark:text-red-400 font-bold' : textColor}`}>
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
    return (
      <div className="flex items-center pb-5 px-1">
        <div className={`h-0.5 w-8 ${bgColor}`} />
      </div>
    )
  }

  const afterEmulator = failurePoint === 'emulator'
  const afterSimulator = failurePoint === 'emulator' || failurePoint === 'simulator'
  const afterGps = failurePoint !== null

  return (
    <div className="p-4">
      <div className="flex items-start">
        <div className="flex-1 flex justify-center">
          <NodeBox icon="📊" label="Dashboard" status={dashboardOk} isFailed={false} isAfterFailure={false} />
        </div>
        <Connector ok={emulatorOk} isAfterFailure={false} />
        <div className="flex-1 flex justify-center">
          <NodeBox icon="🖥️" label="Emulator" status={emulatorOk} isFailed={failurePoint === 'emulator'} isAfterFailure={false} />
        </div>
        <Connector ok={simulatorOk} isAfterFailure={afterEmulator} />
        <div className="flex-1 flex justify-center">
          <NodeBox icon="✈️" label="Simulator" status={simulatorOk} isFailed={failurePoint === 'simulator'} isAfterFailure={afterEmulator} />
        </div>
        <Connector ok={gpsDataOk} isAfterFailure={afterSimulator} />
        <div className="flex-1 flex justify-center">
          <NodeBox icon="🛰️" label="GPS Data" status={gpsDataOk} isFailed={failurePoint === 'gps'} isAfterFailure={afterSimulator} />
        </div>
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
