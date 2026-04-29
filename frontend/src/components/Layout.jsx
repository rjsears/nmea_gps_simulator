// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// Layout.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { LogOut, Sun, Moon } from 'lucide-react'

export default function Layout({ children }) {
  const { logout } = useAuth()
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') || 'system'
    }
    return 'system'
  })

  // Track actual dark mode state for icon display
  const [isDark, setIsDark] = useState(false)

  const toggleTheme = () => {
    // Simple toggle: if currently dark, go light; if light, go dark
    setTheme(isDark ? 'light' : 'dark')
  }

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement
    localStorage.setItem('theme', theme)

    let dark = false
    if (theme === 'dark') {
      dark = true
    } else if (theme === 'light') {
      dark = false
    } else {
      // System preference
      dark = window.matchMedia('(prefers-color-scheme: dark)').matches
    }

    if (dark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    setIsDark(dark)
  }, [theme])

  // Icon shows current actual mode (Sun for light, Moon for dark)
  const ThemeIcon = isDark ? Moon : Sun

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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <img
                src="/LOFT_logo_130x100.png"
                alt="LOFT"
                className="h-10 w-auto"
              />
              <span className="text-lg font-medium text-gray-700 dark:text-gray-300">
                GPS Emulator
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                <ThemeIcon className="h-5 w-5" />
              </button>

              {/* User / Logout */}
              <div className="flex items-center gap-3 ml-2 pl-4 border-l border-gray-200 dark:border-gray-700">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  admin
                </span>
                <button
                  onClick={logout}
                  className="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="Logout"
                >
                  <LogOut className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="relative z-10 -mt-4 pb-2 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>NMEA GPS Emulator v1.0.0 • Richard J. Sears ©2026 • richardjsears@protonmail.com</p>
      </footer>
    </div>
  )
}
