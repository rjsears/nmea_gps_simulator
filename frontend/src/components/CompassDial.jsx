// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
// CompassDial.jsx
//
// Part of the "NMEA GPS Simulator" suite
// Version 1.0.0 - April 10th, 2026
//
// Richard J. Sears
// richardjsears@protonmail.com
// https://github.com/rjsears
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import { useRef, useState } from 'react'

export default function CompassDial({ heading, onChange, disabled, size = 120 }) {
  const svgRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleMouseDown = (e) => {
    if (disabled) return
    setDragging(true)
    updateHeading(e)
  }

  const handleMouseMove = (e) => {
    if (!dragging || disabled) return
    updateHeading(e)
  }

  const handleMouseUp = () => {
    setDragging(false)
  }

  const updateHeading = (e) => {
    const svg = svgRef.current
    if (!svg) return

    const rect = svg.getBoundingClientRect()
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2

    const angle = Math.atan2(e.clientY - cy, e.clientX - cx) * (180 / Math.PI)
    let newHeading = Math.round((angle + 90 + 360) % 360)
    // Convert 0 to 360 (North)
    if (newHeading === 0) newHeading = 360
    onChange(newHeading)
  }

  const r = size / 2 - 10
  const needleLength = r - 10
  const needleAngle = (heading - 90) * (Math.PI / 180)
  const needleX = Math.cos(needleAngle) * needleLength
  const needleY = Math.sin(needleAngle) * needleLength

  return (
    <div className="flex flex-col items-center">
      <svg
        ref={svgRef}
        width={size}
        height={size}
        className={`cursor-pointer ${disabled ? 'opacity-50' : ''}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Outer circle */}
        <circle cx={size/2} cy={size/2} r={r} fill="none" className="stroke-gray-300 dark:stroke-gray-600" strokeWidth="2" />

        {/* Cardinal directions */}
        {['N', 'E', 'S', 'W'].map((dir, i) => {
          const angle = (i * 90 - 90) * (Math.PI / 180)
          const x = size/2 + Math.cos(angle) * (r - 15)
          const y = size/2 + Math.sin(angle) * (r - 15)
          return (
            <text key={dir} x={x} y={y} textAnchor="middle" dominantBaseline="central" className="fill-gray-500 dark:fill-gray-400 text-xs font-bold">
              {dir}
            </text>
          )
        })}

        {/* Tick marks */}
        {[...Array(36)].map((_, i) => {
          const angle = (i * 10 - 90) * (Math.PI / 180)
          const x1 = size/2 + Math.cos(angle) * (r - 5)
          const y1 = size/2 + Math.sin(angle) * (r - 5)
          const x2 = size/2 + Math.cos(angle) * r
          const y2 = size/2 + Math.sin(angle) * r
          return (
            <line
              key={i}
              x1={x1} y1={y1} x2={x2} y2={y2}
              className={i % 9 === 0 ? 'stroke-gray-400 dark:stroke-gray-500' : 'stroke-gray-300 dark:stroke-gray-600'}
              strokeWidth={i % 9 === 0 ? 2 : 1}
            />
          )
        })}

        {/* Needle */}
        <line x1={size/2} y1={size/2} x2={size/2 + needleX} y2={size/2 + needleY} stroke="#3B82F6" strokeWidth="3" strokeLinecap="round" />

        {/* Center dot */}
        <circle cx={size/2} cy={size/2} r="4" fill="#3B82F6" />
      </svg>
      {/* Heading text below compass */}
      <div className="text-sm font-bold text-gray-700 dark:text-gray-300 mt-1">{heading}°</div>
    </div>
  )
}
