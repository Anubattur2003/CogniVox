import React, { useState, useEffect } from 'react'

interface InfoPanelProps {
  className?: string
}

const InfoPanel: React.FC<InfoPanelProps> = ({ className = '' }) => {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [issPosition, setIssPosition] = useState({ lat: 0, lon: 0 })
  const [earthStats, setEarthStats] = useState({
    population: '8.1 billion',
    surfaceTemp: '15°C',
    oceanCoverage: '71%',
    activeSatellites: '8,000+'
  })

  // Calculate current day/night info for India
  const getSunInfo = () => {
    const now = new Date()
    const utcHours = now.getUTCHours() + now.getUTCMinutes() / 60
    
    // India timezone (IST = UTC + 5:30)
    const indiaHours = (utcHours + 5.5) % 24
    
    // Calculate if it's day or night in India
    const isDayInIndia = indiaHours >= 6 && indiaHours <= 18
    
    // Calculate sun position relative to India (77°E longitude)
    const sunLongitude = (utcHours - 12) * 15
    const indiaLongitude = 77
    const sunRelativeToIndia = sunLongitude - indiaLongitude
    
    // Calculate solar declination
    const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24))
    const sunDeclination = 23.45 * Math.sin(Math.PI * 2 * (dayOfYear - 81) / 365)
    
    return {
      longitude: sunRelativeToIndia.toFixed(1),
      declination: sunDeclination.toFixed(1),
      isDay: isDayInIndia,
      indiaTime: indiaHours,
      localTimeString: new Date(now.getTime() + 5.5 * 60 * 60 * 1000).toISOString().replace('T', ' ').slice(0, 19)
    }
  }

  const sunInfo = getSunInfo()

  useEffect(() => {
    // Update current time every second
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    // Simulate ISS position updates
    const issInterval = setInterval(() => {
      setIssPosition(prev => ({
        lat: Math.sin(Date.now() / 60000) * 50, // Simulate orbit
        lon: (prev.lon + 0.25) % 360 - 180
      }))
    }, 1000)

    return () => {
      clearInterval(timeInterval)
      clearInterval(issInterval)
    }
  }, [])

  return (
    <div className={`bg-black bg-opacity-70 text-white p-4 rounded-lg backdrop-blur-sm ${className}`}>
      <h3 className="text-lg font-bold mb-3 text-blue-400">Earth Live Data</h3>
      
      {/* Current Time */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-300">Current Time</h4>
        <p className="text-green-400 font-mono text-xs">
          UTC: {currentTime.toISOString().replace('T', ' ').slice(0, 19)}
        </p>
        <p className="text-cyan-400 font-mono text-sm font-bold">
          🇮🇳 IST: {sunInfo.localTimeString.slice(11)}
        </p>
      </div>

      {/* India Day/Night Status */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-300">India Status</h4>
        <p className={`font-bold text-lg ${sunInfo.isDay ? 'text-yellow-400' : 'text-blue-400'}`}>
          🇮🇳 {sunInfo.isDay ? '☀️ Daytime' : '🌙 Nighttime'}
        </p>
        <p className="text-orange-400 text-xs">
          Sun relative to India: {sunInfo.longitude}°
        </p>
        <p className="text-orange-400 text-xs">
          Solar declination: {sunInfo.declination}°
        </p>
      </div>

      {/* ISS Position */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-300">ISS Position</h4>
        <p className="text-yellow-400">
          Lat: {issPosition.lat.toFixed(2)}°
        </p>
        <p className="text-yellow-400">
          Lon: {issPosition.lon.toFixed(2)}°
        </p>
      </div>

      {/* Earth Statistics */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-300">Earth Stats</h4>
        <div className="space-y-1 text-sm">
          <p><span className="text-cyan-400">Population:</span> {earthStats.population}</p>
          <p><span className="text-cyan-400">Avg Temp:</span> {earthStats.surfaceTemp}</p>
          <p><span className="text-cyan-400">Ocean:</span> {earthStats.oceanCoverage}</p>
          <p><span className="text-cyan-400">Satellites:</span> {earthStats.activeSatellites}</p>
        </div>
      </div>

      {/* Objects Legend */}
      <div>
        <h4 className="text-sm font-semibold text-gray-300 mb-2">Objects Legend</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-yellow-300 rounded-full mr-2"></div>
            <span>☀️ Sun (Real-time position)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-yellow-400 rounded-full mr-2"></div>
            <span>🛰️ ISS (International Space Station)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-400 rounded-full mr-2"></div>
            <span>📡 Other Satellites</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-gray-300 rounded-full mr-2"></div>
            <span>🌙 Moon</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InfoPanel 