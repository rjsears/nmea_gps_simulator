// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// StartStopButton.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { Play, Square, AlertCircle } from 'lucide-react'

export default function StartStopButton({ isRunning, onStart, onStop, disabled, disabledReason }) {
  const handleClick = () => {
    if (isRunning) {
      onStop()
    } else {
      onStart()
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={disabled}
        title={disabled && disabledReason ? disabledReason : undefined}
        className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all shadow-lg ${
          isRunning
            ? 'bg-red-600 hover:bg-red-700 text-white'
            : 'bg-green-600 hover:bg-green-700 text-white'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {isRunning ? (
          <>
            <Square className="w-6 h-6" />
            <span>Stop Emulator</span>
          </>
        ) : (
          <>
            <Play className="w-6 h-6" />
            <span>Start Emulator</span>
          </>
        )}
      </button>
      {disabled && disabledReason && (
        <div className="mt-3 p-2 bg-amber-100 dark:bg-amber-900/50 border border-amber-500 rounded-lg flex items-center justify-center gap-2 text-sm text-amber-700 dark:text-amber-300 font-medium">
          <AlertCircle className="w-5 h-5" />
          <span>{disabledReason}</span>
        </div>
      )}
    </div>
  )
}
