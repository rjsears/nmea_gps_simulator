import { useState, useEffect, useRef } from 'react'
import SimulatorCard from './components/SimulatorCard'

// Simple Sun/Moon icons
const SunIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
  </svg>
)

const MoonIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
  </svg>
)

const HealthIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
)

function App() {
  const [simulators, setSimulators] = useState([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  // Dark mode state
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('dashboard-theme') || 'system'
    }
    return 'system'
  })
  const [isDark, setIsDark] = useState(false)
  const [showHealth, setShowHealth] = useState(false)

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark')
  }

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement
    localStorage.setItem('dashboard-theme', theme)

    let dark = false
    if (theme === 'dark') {
      dark = true
    } else if (theme === 'light') {
      dark = false
    } else {
      dark = window.matchMedia('(prefers-color-scheme: dark)').matches
    }

    if (dark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    setIsDark(dark)
  }, [theme])

  useEffect(() => {
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws`

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'fleet_state') {
            setSimulators(data.simulators)
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 2000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return (
    <div
      className="min-h-screen relative"
      style={{
        backgroundImage: 'url(/map_background.gif)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >
      {/* Dark mode overlay */}
      <div className="absolute inset-0 bg-gray-900/70 dark:block hidden" style={{ backgroundAttachment: 'fixed' }} />

      {/* Header */}
      <header className="relative z-10 bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <img
                src="/LOFT_logo_130x100.png"
                alt="LOFT Logo"
                className="h-12 w-auto"
              />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Fleet Dashboard</h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">Real-time simulator monitoring</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              {/* Health toggle */}
              <button
                onClick={() => setShowHealth(!showHealth)}
                className={`p-2 rounded-lg transition-colors ${
                  showHealth
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title={showHealth ? 'Show position data' : 'Show health status'}
              >
                <HealthIcon />
              </button>
              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDark ? <MoonIcon /> : <SunIcon />}
              </button>
              {/* Connection status */}
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                connected
                  ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300'
                  : 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300'
              }`}>
                <span className={`w-2 h-2 rounded-full mr-2 ${
                  connected ? 'bg-green-500' : 'bg-red-500'
                }`}></span>
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {simulators.length === 0 ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-500 dark:text-gray-400">Waiting for simulator data...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {simulators.map((sim) => (
              <SimulatorCard key={sim.port} simulator={sim} showHealth={showHealth} />
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative z-10 fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-2">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-gray-400 dark:text-gray-500">
            LOFT Fleet Dashboard v1.0.0 • Richard J. Sears ©2026 • richardjsears@protonmail.com • {simulators.length} simulators configured
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
