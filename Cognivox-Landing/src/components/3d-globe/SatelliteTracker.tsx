import React, { useRef, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface SatelliteData {
  id: string
  name: string
  latitude: number
  longitude: number
  altitude: number
  velocity: number
}

function SatelliteTracker() {
  const groupRef = useRef<THREE.Group>(null)
  const [satellites, setSatellites] = useState<SatelliteData[]>([])

  // Mock satellite data (in a real app, you'd fetch from an API like N2YO or similar)
  const mockSatelliteData: SatelliteData[] = [
    {
      id: 'iss',
      name: 'International Space Station',
      latitude: 45.0,
      longitude: 0.0,
      altitude: 408,
      velocity: 7.66
    },
    {
      id: 'hubble',
      name: 'Hubble Space Telescope',
      latitude: -23.5,
      longitude: 45.0,
      altitude: 547,
      velocity: 7.59
    },
    {
      id: 'gps1',
      name: 'GPS Satellite',
      latitude: 0.0,
      longitude: 90.0,
      altitude: 20200,
      velocity: 3.87
    }
  ]

  useEffect(() => {
    // Simulate real-time data updates
    const interval = setInterval(() => {
      setSatellites(prevSats => 
        prevSats.map(sat => ({
          ...sat,
          longitude: (sat.longitude + sat.velocity * 0.01) % 360
        }))
      )
    }, 1000)

    // Initialize with mock data
    setSatellites(mockSatelliteData)

    return () => clearInterval(interval)
  }, [])

  // Convert lat/lon to 3D position
  const latLonToVector3 = (lat: number, lon: number, altitude: number, radius: number = 2) => {
    const phi = (90 - lat) * (Math.PI / 180)
    const theta = (lon + 180) * (Math.PI / 180)
    const earthRadius = radius + (altitude / 6371) // altitude in km, Earth radius ~6371km
    
    const x = -(earthRadius * Math.sin(phi) * Math.cos(theta))
    const z = (earthRadius * Math.sin(phi) * Math.sin(theta))
    const y = (earthRadius * Math.cos(phi))
    
    return new THREE.Vector3(x, y, z)
  }

  useFrame((state) => {
    if (groupRef.current) {
      // Optional: make satellites pulse
      const time = state.clock.getElapsedTime()
      groupRef.current.children.forEach((child, index) => {
        if (child instanceof THREE.Mesh) {
          const material = child.material as THREE.MeshBasicMaterial
          material.opacity = 0.7 + 0.3 * Math.sin(time * 2 + index)
        }
      })
    }
  })

  return (
    <group ref={groupRef}>
      {satellites.map((satellite, index) => {
        const position = latLonToVector3(satellite.latitude, satellite.longitude, satellite.altitude)
        
        return (
          <group key={satellite.id}>
            {/* Satellite dot */}
            <mesh position={position}>
              <sphereGeometry args={[0.02, 8, 8]} />
              <meshBasicMaterial 
                color={satellite.name.includes('ISS') ? '#ffff00' : '#ff4444'} 
                transparent
                opacity={0.8}
              />
            </mesh>
            
            {/* Orbit line for ISS */}
            {satellite.name.includes('ISS') && (
              <line>
                <bufferGeometry>
                  <bufferAttribute
                    attach="attributes-position"
                    count={64}
                    array={new Float32Array(
                      Array.from({ length: 64 }, (_, i) => {
                        const angle = (i / 64) * Math.PI * 2
                        const orbitPos = latLonToVector3(
                          satellite.latitude,
                          angle * (180 / Math.PI),
                          satellite.altitude
                        )
                        return [orbitPos.x, orbitPos.y, orbitPos.z]
                      }).flat()
                    )}
                    itemSize={3}
                  />
                </bufferGeometry>
                <lineBasicMaterial color="#ffff00" opacity={0.3} transparent />
              </line>
            )}
          </group>
        )
      })}
    </group>
  )
}

export default SatelliteTracker 