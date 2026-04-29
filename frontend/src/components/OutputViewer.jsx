// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// OutputViewer.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useState, useEffect, useRef } from 'react'
import { Terminal, Trash2, Pause, Play } from 'lucide-react'

export default function OutputViewer({ isRunning, isReceiver = false }) {
  const [messages, setMessages] = useState([])
  const [paused, setPaused] = useState(false)
  const pausedRef = useRef(paused)
  const containerRef = useRef(null)
  const maxMessages = 100

  // Keep ref in sync with state
  useEffect(() => {
    pausedRef.current = paused
  }, [paused])

  const title = isReceiver ? 'NMEA Input' : 'NMEA Output'

  // Connect to WebSocket and listen for NMEA output
  useEffect(() => {
    if (!isRunning) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'nmea_output' && data.sentences) {
          // Skip adding messages when paused
          if (pausedRef.current) return

          const timestamp = new Date().toLocaleTimeString()
          setMessages(prev => {
            const newMessages = [
              ...prev,
              ...data.sentences.map(s => ({ time: timestamp, text: s.trim() }))
            ]
            // Keep only the last maxMessages
            return newMessages.slice(-maxMessages)
          })
        }
      } catch (e) {
        // Ignore non-JSON messages
      }
    }

    return () => {
      ws.close()
    }
  }, [isRunning])

  // Auto-scroll to bottom (only when not paused)
  useEffect(() => {
    if (containerRef.current && !paused) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages, paused])

  const clearMessages = () => setMessages([])

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Terminal className="w-5 h-5 text-green-500" />
          {title}
        </h2>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPaused(!paused)}
            className={`p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors ${paused ? 'text-yellow-500' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}
            title={paused ? "Resume auto-scroll" : "Pause auto-scroll"}
          >
            {paused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          </button>
          <button
            onClick={clearMessages}
            className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            title="Clear output"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        className="bg-gray-900 dark:bg-black rounded-lg p-3 h-48 overflow-y-auto font-mono text-xs scrollbar-thin"
      >
        {!isRunning ? (
          <div className="text-gray-500 text-center py-8">
            {isReceiver
              ? 'Start the emulator to see incoming NMEA data'
              : 'Start the emulator to see NMEA output'
            }
          </div>
        ) : messages.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            Waiting for data...
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className="text-green-400 leading-relaxed">
              <span className="text-gray-500">{msg.time}</span>{' '}
              <span>{msg.text}</span>
            </div>
          ))
        )}
      </div>

      {isRunning && messages.length > 0 && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {messages.length} messages (showing last {maxMessages})
        </div>
      )}
    </div>
  )
}
