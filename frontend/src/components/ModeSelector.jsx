// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// ModeSelector.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { Radio, Send, Download, Repeat, Usb } from 'lucide-react'

export default function ModeSelector({ modes, onChange, disabled }) {
  const handleChange = (key, value) => {
    let newModes = { ...modes, [key]: value }

    // Stand Alone mode logic
    if (key === 'standalone' && value) {
      // Stand Alone disables other modes (USB output is now optional)
      newModes.sender = false
      newModes.receiver = false
      newModes.rebroadcaster = false
    }

    // Sender mode logic - cannot combine with Stand Alone or Receiver
    if (key === 'sender' && value) {
      newModes.standalone = false
      newModes.receiver = false
      newModes.rebroadcaster = false
      newModes.usb_output = false
    }

    // Receiver mode logic - cannot combine with Stand Alone or Sender
    if (key === 'receiver' && value) {
      newModes.standalone = false
      newModes.sender = false
    }

    // If Receiver is unchecked, also uncheck Rebroadcaster
    if (key === 'receiver' && !value) {
      newModes.rebroadcaster = false
    }

    // Rebroadcaster requires Receiver to be enabled
    if (key === 'rebroadcaster' && value) {
      // Rebroadcaster is only valid with Receiver
      if (!modes.receiver) {
        return // Don't allow enabling if Receiver isn't checked
      }
      // Clear usb_output since rebroadcaster has its own USB option
      newModes.usb_output = false
    }

    onChange(newModes)
  }

  // Determine what's disabled based on current selections
  const standaloneDisabled = disabled || modes.sender || modes.receiver
  const senderDisabled = disabled || modes.standalone || modes.receiver
  const receiverDisabled = disabled || modes.standalone || modes.sender

  // Rebroadcaster requires Receiver to be selected
  const rebroadcasterDisabled = disabled || !modes.receiver

  // USB output option is only shown when not in standalone mode (standalone has its own output config)
  const usbOutputDisabled = disabled

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Operating Mode</h2>

      <div className="space-y-3">
        {/* Stand Alone Mode */}
        <label className={`flex items-center gap-3 cursor-pointer ${standaloneDisabled ? 'opacity-50' : ''}`}>
          <input
            type="checkbox"
            checked={modes.standalone}
            onChange={(e) => handleChange('standalone', e.target.checked)}
            disabled={standaloneDisabled}
            className="w-5 h-5 rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-blue-600 focus:ring-blue-500"
          />
          <Radio className="w-5 h-5 text-blue-500" />
          <span className="text-gray-900 dark:text-white">Stand Alone</span>
          <span className="text-gray-500 dark:text-gray-400 text-sm ml-auto">Generate GPS Data</span>
        </label>

        {/* Sender Mode */}
        <label className={`flex items-center gap-3 cursor-pointer ${senderDisabled ? 'opacity-50' : ''}`}>
          <input
            type="checkbox"
            checked={modes.sender}
            onChange={(e) => handleChange('sender', e.target.checked)}
            disabled={senderDisabled}
            className="w-5 h-5 rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-blue-600 focus:ring-blue-500"
          />
          <Send className="w-5 h-5 text-blue-500" />
          <span className="text-gray-900 dark:text-white">Sender</span>
          <span className="text-gray-500 dark:text-gray-400 text-sm ml-auto">Broadcast to Receiver(s)</span>
        </label>

        {/* Receiver Mode */}
        <label className={`flex items-center gap-3 cursor-pointer ${receiverDisabled ? 'opacity-50' : ''}`}>
          <input
            type="checkbox"
            checked={modes.receiver}
            onChange={(e) => handleChange('receiver', e.target.checked)}
            disabled={receiverDisabled}
            className="w-5 h-5 rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-blue-600 focus:ring-blue-500"
          />
          <Download className="w-5 h-5 text-blue-500" />
          <span className="text-gray-900 dark:text-white">Receiver</span>
          <span className="text-gray-500 dark:text-gray-400 text-sm ml-auto">Listen for Data</span>
        </label>

        {/* Rebroadcaster Option - shown as sub-option when Receiver is selected */}
        {modes.receiver && (
          <label className={`flex items-center gap-3 cursor-pointer ml-8 ${rebroadcasterDisabled ? 'opacity-50' : ''}`}>
            <input
              type="checkbox"
              checked={modes.rebroadcaster}
              onChange={(e) => handleChange('rebroadcaster', e.target.checked)}
              disabled={rebroadcasterDisabled}
              className="w-5 h-5 rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-purple-600 focus:ring-purple-500"
            />
            <Repeat className="w-5 h-5 text-purple-500" />
            <span className="text-gray-900 dark:text-white">Rebroadcaster</span>
            <span className="text-gray-500 dark:text-gray-400 text-sm ml-auto">Rebroadcast to EFB/USB</span>
          </label>
        )}

        {/* USB Output Option - only shown for Receiver mode (without Rebroadcaster) */}
        {/* Other modes have their own USB options in their config panels */}
        {modes.receiver && !modes.rebroadcaster && (
          <>
            <hr className="border-gray-200 dark:border-gray-700 my-3" />
            <label className={`flex items-center gap-3 cursor-pointer ${usbOutputDisabled ? 'opacity-50' : ''}`}>
              <input
                type="checkbox"
                checked={modes.usb_output}
                onChange={(e) => handleChange('usb_output', e.target.checked)}
                disabled={usbOutputDisabled}
                className="w-5 h-5 rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-blue-600 focus:ring-blue-500"
              />
              <Usb className="w-5 h-5 text-green-500" />
              <span className="text-gray-900 dark:text-white">Output to USB?</span>
            </label>
          </>
        )}
      </div>
    </div>
  )
}
