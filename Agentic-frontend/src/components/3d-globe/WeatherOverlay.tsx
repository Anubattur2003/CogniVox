import React, { useRef, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface WeatherData {
  lat: number
  lon: number
  type: 'storm' | 'clear' | 'cloudy' | 'rain'
  intensity: number
}

function WeatherOverlay() {
  const groupRef = useRef<THREE.Group>(null)
  const [weatherData, setWeatherData] = useState<WeatherData[]>([])

  // Mock weather data (in production, you'd fetch from OpenWeather API or similar)
  const generateMockWeatherData = (): WeatherData[] => {
    const data: WeatherData[] = []
    
    // Generate random weather patterns
    for (let i = 0; i < 50; i++) {
      data.push({
        lat: (Math.random() - 0.5) * 180,
        lon: (Math.random() - 0.5) * 360,
        type: ['storm', 'clear', 'cloudy', 'rain'][Math.floor(Math.random() * 4)] as WeatherData['type'],
        intensity: Math.random()
      })
    }
    
    return data
  }

  useEffect(() => {
    // Initialize weather data
    setWeatherData(generateMockWeatherData())
    
    // Update weather data every 30 seconds
    const interval = setInterval(() => {
      setWeatherData(generateMockWeatherData())
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  // Convert lat/lon to 3D position on Earth surface
  const latLonToVector3 = (lat: number, lon: number, radius: number = 2.02) => {
    const phi = (90 - lat) * (Math.PI / 180)
    const theta = (lon + 180) * (Math.PI / 180)
    
    const x = -(radius * Math.sin(phi) * Math.cos(theta))
    const z = (radius * Math.sin(phi) * Math.sin(theta))
    const y = (radius * Math.cos(phi))
    
    return new THREE.Vector3(x, y, z)
  }

  // Get color based on weather type
  const getWeatherColor = (type: WeatherData['type']): string => {
    switch (type) {
      case 'storm': return '#ff0000'
      case 'rain': return '#0066ff'
      case 'cloudy': return '#cccccc'
      case 'clear': return '#ffff00'
      default: return '#ffffff'
    }
  }

  useFrame((state) => {
    if (groupRef.current) {
      const time = state.clock.getElapsedTime()
      groupRef.current.children.forEach((child, index) => {
        if (child instanceof THREE.Mesh) {
          // Animate weather patterns
          const material = child.material as THREE.MeshBasicMaterial
          const baseOpacity = 0.3 + weatherData[index]?.intensity * 0.4
          material.opacity = baseOpacity + 0.2 * Math.sin(time * 2 + index)
        }
      })
    }
  })

  return (
    <group ref={groupRef}>
      {weatherData.map((weather, index) => {
        const position = latLonToVector3(weather.lat, weather.lon)
        const size = 0.05 + weather.intensity * 0.1
        
        return (
          <mesh key={index} position={position}>
            <sphereGeometry args={[size, 8, 8]} />
            <meshBasicMaterial 
              color={getWeatherColor(weather.type)}
              transparent
              opacity={0.3 + weather.intensity * 0.4}
            />
          </mesh>
        )
      })}
    </group>
  )
}

export default WeatherOverlay 