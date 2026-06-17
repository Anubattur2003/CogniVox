import React, { useRef, useEffect, useState } from 'react'
import { Canvas, useFrame, useLoader, useThree } from '@react-three/fiber'
import { OrbitControls, Stars } from '@react-three/drei'
import * as THREE from 'three'
import SatelliteTracker from './SatelliteTracker'
import InfoPanel from './InfoPanel'

// Custom OrbitControls component that respects lockPosition
function CustomOrbitControls({
  enablePan,
  enableZoom,
  maxDistance,
  minDistance,
  autoRotate,
  autoRotateSpeed,
  enableDamping,
  dampingFactor,
  lockPosition = false,
  cameraPosition
}: {
  enablePan?: boolean
  enableZoom?: boolean
  maxDistance?: number
  minDistance?: number
  autoRotate?: boolean
  autoRotateSpeed?: number
  enableDamping?: boolean
  dampingFactor?: number
  lockPosition?: boolean
  cameraPosition?: [number, number, number]
}) {
  const { camera } = useThree()
  const controlsRef = useRef<any>()

  useEffect(() => {
    if (cameraPosition) {
      camera.position.set(cameraPosition[0], cameraPosition[1], cameraPosition[2])
      camera.lookAt(0, 0, 0)
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0)
        controlsRef.current.update()
      }
    }
  }, [cameraPosition, camera])

  return (
    <OrbitControls
      ref={controlsRef}
      enablePan={!lockPosition && enablePan}
      enableZoom={!lockPosition && enableZoom}
      enableRotate={!lockPosition}
      maxDistance={maxDistance}
      minDistance={minDistance}
      autoRotate={autoRotate}
      autoRotateSpeed={autoRotateSpeed}
      enableDamping={enableDamping}
      dampingFactor={dampingFactor}
    />
  )
}

// TypeScript interfaces for component props
export interface EarthGlobeProps {
  showBackground?: boolean
  showGlobe?: boolean
  showInfo?: boolean
  showSun?: boolean
  showMoon?: boolean
  showSatellites?: boolean
  showStars?: boolean
  className?: string
  width?: string | number
  height?: string | number
  cameraPosition?: [number, number, number]
  autoRotate?: boolean
  autoRotateSpeed?: number
  enableZoom?: boolean
  enablePan?: boolean
  lockPosition?: boolean
  maxDistance?: number
  minDistance?: number
}

export interface EarthComponentProps {
  showSun?: boolean
  showMoon?: boolean
  showSatellites?: boolean
}

// Earth component with realistic textures
function Earth({ showSun = true, showMoon = true, showSatellites = true }: EarthComponentProps) {
  const earthGroupRef = useRef<THREE.Group>(null)
  const [isUserInteracting, setIsUserInteracting] = useState(false)

  // Use working Earth texture URLs including night lights
  const [colorMap, normalMap, specularMap, cloudsMap, nightMap] = useLoader(THREE.TextureLoader, [
    'https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg',
    'https://threejs.org/examples/textures/planets/earth_normal_2048.jpg',
    'https://threejs.org/examples/textures/planets/earth_specular_2048.jpg',
    'https://threejs.org/examples/textures/planets/earth_clouds_1024.png',
    'https://threejs.org/examples/textures/planets/earth_lights_2048.png'
  ])

  // Smart rotation system that maintains accuracy
  useFrame((state, delta) => {
    if (earthGroupRef.current) {
      if (isUserInteracting) {
        // When user is interacting, maintain the current day/night accuracy
        // but allow manual rotation to override visual positioning
        const accurateRotation = getAccurateEarthRotation()
        // Store the base accurate rotation, user interaction will add to this
        earthGroupRef.current.userData.baseRotation = accurateRotation
      } else {
        // When not interacting, show accurate Earth rotation with gentle auto-rotation
        const accurateRotation = getAccurateEarthRotation()
        const visualRotation = state.clock.getElapsedTime() * 0.05 // Slower visual rotation

        // Apply both rotations: accurate time-based + gentle visual auto-rotation
        earthGroupRef.current.rotation.y = accurateRotation + visualRotation
      }
    }
  })

  useEffect(() => {
    const handleInteractionStart = () => setIsUserInteracting(true)
    const handleInteractionEnd = () => {
      setTimeout(() => setIsUserInteracting(false), 2000) // Resume auto-rotation after 2s
    }

    window.addEventListener('mousedown', handleInteractionStart)
    window.addEventListener('mouseup', handleInteractionEnd)
    window.addEventListener('wheel', handleInteractionStart)

    return () => {
      window.removeEventListener('mousedown', handleInteractionStart)
      window.removeEventListener('mouseup', handleInteractionEnd)
      window.removeEventListener('wheel', handleInteractionStart)
    }
  }, [])

  return (
    <group>
      {/* Main rotating Earth group - all textures rotate together */}
      <group ref={earthGroupRef}>
        {/* Main Earth Sphere with Day texture */}
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[2, 64, 64]} />
          <meshLambertMaterial
            map={colorMap}
            normalMap={normalMap}
            color="#ffffff"
          />
        </mesh>

        {/* Night side with city lights - rotates with Earth */}
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[2.001, 64, 64]} />
          <meshBasicMaterial
            map={nightMap}
            transparent
            opacity={0}
            blending={THREE.AdditiveBlending}
            color="#ffcc66"
          />
        </mesh>

        {/* Clouds Layer - rotates with Earth */}
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[2.01, 64, 64]} />
          <meshPhongMaterial
            map={cloudsMap}
            transparent
            opacity={0.4}
            alphaMap={cloudsMap}
            color="#ffffff"
          />
        </mesh>
      </group>

      {/* Atmosphere Glow - doesn't rotate */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[2.15, 64, 64]} />
        <meshPhongMaterial
          color="#87CEEB"
          transparent
          opacity={0.25}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Conditionally render celestial objects */}
      {showSun && <SunIndicator />}
      {showMoon && <Moon />}
      {showSatellites && <SatelliteTracker />}
    </group>
  )
}

// Moon component with realistic orbital motion that's visible from any angle
function Moon() {
  const moonRef = useRef<THREE.Mesh>(null)

  // Load moon texture from Three.js examples
  const moonTexture = useLoader(THREE.TextureLoader,
    'https://threejs.org/examples/textures/planets/moon_1024.jpg'
  )

  useFrame((state) => {
    if (moonRef.current) {
      // Moon orbiting around Earth with consistent motion
      const time = state.clock.getElapsedTime()
      const orbitRadius = 12
      const orbitSpeed = 0.03 // Slower, more realistic speed

      // Consistent orbital motion that looks good from any camera angle
      const moonAngle = time * orbitSpeed
      moonRef.current.position.x = Math.cos(moonAngle) * orbitRadius
      moonRef.current.position.z = Math.sin(moonAngle) * orbitRadius
      moonRef.current.position.y = Math.sin(moonAngle * 0.2) * 1.5 // Gentle vertical variation

      // Moon rotation on its axis (tidally locked like real moon)
      moonRef.current.rotation.y = moonAngle // Same as orbital period
      moonRef.current.rotation.x += 0.001
    }
  })

  return (
    <mesh ref={moonRef}>
      <sphereGeometry args={[0.35, 32, 32]} />
      <meshPhongMaterial
        map={moonTexture}
        shininess={5}
        specular={new THREE.Color(0x222222)}
      />
    </mesh>
  )
}

// Fixed sun position - sun doesn't move, only Earth rotates
function getFixedSunPosition() {
  const now = new Date()

  // Calculate sun's declination (changes with seasons)
  const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24))
  const sunDeclination = 23.45 * Math.sin(Math.PI * 2 * (dayOfYear - 81) / 365)

  // Sun position: always points from the side (like solar noon at Greenwich)
  // This creates a proper day/night terminator
  const phi = (90 - sunDeclination) * (Math.PI / 180)
  const theta = 0 // Fixed position - sun always "points" from the right side

  const x = Math.sin(phi) * Math.cos(theta) * 20  // Far away, like real sun
  const z = Math.sin(phi) * Math.sin(theta) * 20
  const y = Math.cos(phi) * 20

  return [x, y, z] as [number, number, number]
}

// Calculate Earth's accurate rotation based on current UTC time
function getAccurateEarthRotation() {
  const now = new Date()
  const utcHours = now.getUTCHours() + now.getUTCMinutes() / 60 + now.getUTCSeconds() / 3600

  // Earth rotates 360° in 24 hours = 15° per hour
  // At UTC 12:00 (noon), Greenwich (0° longitude) should face the sun directly
  // Current implementation: rotate Earth so that the meridian facing the sun 
  // corresponds to where it should be at this UTC time
  const earthRotationAngle = -(utcHours * 15 - 0) * (Math.PI / 180)

  return earthRotationAngle
}

// Sun indicator component positioned accurately relative to lighting direction
function SunIndicator() {
  const sunRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (sunRef.current) {
      // Get the accurate sun position for lighting
      const accurateSunPosition = getFixedSunPosition()

      // Position visual sun indicator at the actual light source direction
      // This ensures it always appears where the sunlight is coming from
      sunRef.current.position.set(
        accurateSunPosition[0],
        accurateSunPosition[1],
        accurateSunPosition[2]
      )

      // Sun rotation on its axis for visual appeal
      sunRef.current.rotation.y += 0.01
      sunRef.current.rotation.x += 0.005
    }
  })

  return (
    <mesh ref={sunRef}>
      <sphereGeometry args={[0.25, 16, 16]} />
      <meshBasicMaterial color="#ffdd44" />
      {/* Add sun glow effect */}
      <pointLight intensity={0.5} color="#ffdd44" distance={10} />
    </mesh>
  )
}

// Lighting setup with absolutely fixed sun position (separate from visual sun indicator)
// This maintains accurate day/night cycles regardless of visual sun rotation
function Lighting() {
  const lightRef = useRef<THREE.DirectionalLight>(null)
  const fixedSunPosition = getFixedSunPosition() // Sun never moves position in space for accurate lighting

  useFrame(() => {
    if (lightRef.current) {
      lightRef.current.position.set(fixedSunPosition[0], fixedSunPosition[1], fixedSunPosition[2])
    }
  })

  const sunPosition = fixedSunPosition

  return (
    <>
      {/* Main sun light - creates day/night terminator */}
      <directionalLight
        ref={lightRef}
        position={sunPosition}
        intensity={2.5}
        color="#ffffff"
        castShadow
        shadow-mapSize-width={4096}
        shadow-mapSize-height={4096}
        shadow-camera-near={0.1}
        shadow-camera-far={100}
        shadow-camera-left={-15}
        shadow-camera-right={15}
        shadow-camera-top={15}
        shadow-camera-bottom={-15}
      />
      {/* Very minimal ambient light - makes night side visible but dark */}
      <ambientLight intensity={2.2} color="#ffffff" />
      <directionalLight position={[3, 2, 6]} intensity={1.5} color="#fff8f0" />
    </>
  )
}

// Main reusable EarthGlobe component
const EarthGlobe: React.FC<EarthGlobeProps> = ({
  showBackground = true,
  showGlobe = true,
  showInfo = true,
  showSun = true,
  showMoon = true,
  showSatellites = true,
  showStars = true,
  className = "",
  width = "100%",
  height = "100%",
  cameraPosition = [2, 1, 4],
  autoRotate = true,
  autoRotateSpeed = 0.2,
  enableZoom = true,
  enablePan = false,
  lockPosition = false,
  maxDistance = 15,
  minDistance = 3
}) => {
  const containerStyle: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
    position: 'relative'
  }

  return (
    <div className={`${showBackground ? 'stars-bg' : ''} ${className}`} style={containerStyle}>
      {showGlobe && (
        <Canvas
          camera={{
            position: cameraPosition,
            fov: 45
          }}
          style={{ background: 'transparent' }}
          onCreated={({ gl, camera }) => {
            gl.setClearColor('#000000', 0)
            camera.lookAt(0, 0, 0) // Look at Earth center
          }}
        >
          {/* Lighting */}
          <Lighting />

          {/* Stars background */}
          {showStars && (
            <Stars
              radius={300}
              depth={60}
              count={20000}
              factor={7}
              saturation={0}
              fade
            />
          )}

          {/* Earth */}
          <Earth
            showSun={showSun}
            showMoon={showMoon}
            showSatellites={showSatellites}
          />

          {/* Controls */}
          <CustomOrbitControls
            enablePan={enablePan}
            enableZoom={enableZoom}
            maxDistance={maxDistance}
            minDistance={minDistance}
            autoRotate={autoRotate}
            autoRotateSpeed={autoRotateSpeed}
            enableDamping={true}
            dampingFactor={0.05}
            lockPosition={lockPosition}
            cameraPosition={cameraPosition}
          />
        </Canvas>
      )}

      {/* Info Panel */}
      {showInfo && <InfoPanel />}
    </div>
  )
}

// Export individual components for granular control
export { Earth, Moon, SunIndicator, Lighting, getFixedSunPosition, getAccurateEarthRotation }

// Export main component as default
export default EarthGlobe 