// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// NavigationControls.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { Plane, Mountain, Compass } from 'lucide-react'
import Slider from './Slider'
import CompassDial from './CompassDial'

export default function NavigationControls({ altitude, speed, heading, onChange, disabled }) {
  return (
    <div className={`card ${disabled ? 'opacity-50' : ''}`}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Navigation</h2>

      <div className="space-y-6">
        <Slider
          label={<span className="flex items-center gap-2"><Mountain className="w-4 h-4 text-blue-500" />Altitude</span>}
          value={altitude}
          onChange={(v) => onChange({ altitude_ft: v })}
          min={0} max={50000} step={100} unit="ft" disabled={disabled}
        />

        <Slider
          label={<span className="flex items-center gap-2"><Plane className="w-4 h-4 text-blue-500" />Airspeed</span>}
          value={speed}
          onChange={(v) => onChange({ speed_kts: v })}
          min={0} max={600} step={5} unit="kts" disabled={disabled}
        />

        <div>
          <label className="label flex items-center gap-2">
            <Compass className="w-4 h-4 text-blue-500" />Heading
          </label>
          <div className="flex items-center gap-4">
            <CompassDial heading={heading} onChange={(v) => onChange({ heading: v })} disabled={disabled} />
            <div className="flex-1">
              <Slider label="" value={heading} onChange={(v) => onChange({ heading: v })} min={1} max={360} step={1} unit="deg" disabled={disabled} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
