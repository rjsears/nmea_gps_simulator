import { useState, useEffect, useCallback } from 'react'

const FORMATS = [
  { value: 'csv', label: 'CSV (spreadsheet)' },
  { value: 'json', label: 'JSON' },
  { value: 'xml', label: 'XML' },
  { value: 'gpx', label: 'GPX (GPS track)' },
  { value: 'kml', label: 'KML (Google Earth)' },
]

// Format a Date as the value a <input type="datetime-local"> expects (local time)
const toLocalInput = (date) => {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const formatBytes = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

const formatTime = (iso) => (iso ? new Date(iso).toLocaleString() : '—')

function FlightDataPanel({ onClose }) {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [start, setStart] = useState(() => toLocalInput(new Date(Date.now() - 2 * 3600 * 1000)))
  const [end, setEnd] = useState(() => toLocalInput(new Date()))
  const [format, setFormat] = useState('csv')
  const [selectedSims, setSelectedSims] = useState(null) // null = all
  const [rowCount, setRowCount] = useState(null)

  const loadStatus = useCallback(async () => {
    try {
      const resp = await fetch('/api/recording')
      if (!resp.ok) throw new Error(`Status ${resp.status}`)
      setStatus(await resp.json())
      setError(null)
    } catch (e) {
      setError(`Could not load recording status: ${e.message}`)
    }
  }, [])

  useEffect(() => {
    loadStatus()
    const timer = setInterval(loadStatus, 5000)
    return () => clearInterval(timer)
  }, [loadStatus])

  const sims = status?.simulators ?? []
  const chosenSims = selectedSims ?? sims.map((s) => s.name)
  const startDate = new Date(start)
  // Pickers have minute precision, so "To" includes that entire minute
  const endDate = new Date(new Date(end).getTime() + 59999)
  const rangeValid = !isNaN(startDate) && !isNaN(endDate) && endDate >= startDate && chosenSims.length > 0

  const query = rangeValid
    ? new URLSearchParams({
        start: startDate.toISOString(),
        end: endDate.toISOString(),
        sims: chosenSims.join(','),
      }).toString()
    : null

  // Preview how many positions the export will contain
  useEffect(() => {
    if (!query) {
      setRowCount(null)
      return
    }
    const controller = new AbortController()
    const timer = setTimeout(async () => {
      try {
        const resp = await fetch(`/api/recording/count?${query}`, { signal: controller.signal })
        if (resp.ok) setRowCount((await resp.json()).rows)
      } catch {
        // aborted or network error; keep the previous value
      }
    }, 300)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [query])

  const toggleRecording = async (name, enabled) => {
    try {
      const resp = await fetch(`/api/recording/${encodeURIComponent(name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      })
      if (!resp.ok) throw new Error(`Status ${resp.status}`)
      loadStatus()
    } catch (e) {
      setError(`Could not change recording for ${name}: ${e.message}`)
    }
  }

  const toggleSelected = (name) => {
    const next = chosenSims.includes(name)
      ? chosenSims.filter((n) => n !== name)
      : [...chosenSims, name]
    setSelectedSims(next)
  }

  const setPreset = (hours) => {
    const now = new Date()
    setEnd(toLocalInput(now))
    setStart(toLocalInput(new Date(now.getTime() - hours * 3600 * 1000)))
  }

  const exportUrl = query ? `/api/recording/export?${query}&format=${format}` : null

  const inputClass =
    'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm'
  const sectionTitle = 'text-sm font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide mb-3'

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 p-4 overflow-y-auto" onClick={onClose}>
      <div
        className="w-full max-w-3xl my-8 rounded-xl bg-white dark:bg-gray-800 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Flight Data</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Record simulator positions and export them by date and time
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
            title="Close"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-8">
          {error && (
            <div className="rounded-lg bg-red-50 dark:bg-red-900/40 text-red-700 dark:text-red-300 px-4 py-2 text-sm">
              {error}
            </div>
          )}

          {/* Recording toggles */}
          <section>
            <h3 className={sectionTitle}>Recording</h3>
            <div className="divide-y divide-gray-200 dark:divide-gray-700 rounded-lg border border-gray-200 dark:border-gray-700">
              {sims.map((sim) => (
                <div key={sim.name} className="flex items-center justify-between px-4 py-2">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{sim.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Last recorded: {formatTime(sim.last_ts)}
                    </p>
                  </div>
                  <button
                    onClick={() => toggleRecording(sim.name, !sim.recording)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      sim.recording ? 'bg-red-600' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                    title={sim.recording ? 'Recording - click to stop' : 'Not recording - click to start'}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        sim.recording ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
            {status && (
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Stored: {formatTime(status.first_ts)} to {formatTime(status.last_ts)} •
                Database size {formatBytes(status.db_size_bytes)} •{' '}
                {status.retention_days > 0
                  ? `Data older than ${status.retention_days} days is deleted automatically`
                  : 'Data is kept forever'}
              </p>
            )}
          </section>

          {/* Export */}
          <section>
            <h3 className={sectionTitle}>Export</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className="block text-sm text-gray-600 dark:text-gray-300">
                From
                <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} className={`${inputClass} mt-1`} />
              </label>
              <label className="block text-sm text-gray-600 dark:text-gray-300">
                To
                <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} className={`${inputClass} mt-1`} />
              </label>
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              {[
                ['Last hour', 1],
                ['Last 4 hours', 4],
                ['Last 24 hours', 24],
                ['Last 7 days', 24 * 7],
                ['Last 30 days', 24 * 30],
              ].map(([label, hours]) => (
                <button
                  key={label}
                  onClick={() => setPreset(hours)}
                  className="px-3 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  {label}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Times are in your local time zone. Exported timestamps are UTC.
            </p>

            <div className="mt-4">
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">Simulators</p>
              <div className="flex flex-wrap gap-3">
                {sims.map((sim) => (
                  <label key={sim.name} className="inline-flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
                    <input
                      type="checkbox"
                      checked={chosenSims.includes(sim.name)}
                      onChange={() => toggleSelected(sim.name)}
                      className="rounded"
                    />
                    {sim.name}
                  </label>
                ))}
              </div>
            </div>

            <div className="mt-4 flex flex-col sm:flex-row sm:items-end gap-4">
              <label className="block text-sm text-gray-600 dark:text-gray-300 sm:w-64">
                Format
                <select value={format} onChange={(e) => setFormat(e.target.value)} className={`${inputClass} mt-1`}>
                  {FORMATS.map((f) => (
                    <option key={f.value} value={f.value}>{f.label}</option>
                  ))}
                </select>
              </label>
              <a
                href={exportUrl && rowCount ? exportUrl : undefined}
                download
                className={`inline-flex justify-center items-center px-5 py-2 rounded-lg font-semibold text-sm ${
                  exportUrl && rowCount
                    ? 'bg-primary-600 hover:bg-primary-700 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed pointer-events-none'
                }`}
              >
                Export
              </a>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {!rangeValid
                  ? 'Pick a valid range and at least one simulator'
                  : rowCount === null
                    ? 'Counting…'
                    : `${rowCount.toLocaleString()} positions`}
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

export default FlightDataPanel
