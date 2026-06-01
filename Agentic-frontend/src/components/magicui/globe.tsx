"use client";

import createGlobe from "cobe";
import { useCallback, useEffect, useRef } from "react";
import { cn } from "../../lib/utils";

// NASA-inspired Realistic Earth configuration (like Miniature Earth)
const REALISTIC_GLOBE_CONFIG = {
  width: 800,
  height: 800,
  onRender: (state: Record<string, any>) => {
    state.phi += 0.002;
  },
  devicePixelRatio: 2,
  phi: 0,
  theta: 0.1,
  dark: 0.2,
  diffuse: 2.4,
  mapSamples: 64000,
  mapBrightness: 3.8,
  baseColor: [0.05, 0.08, 0.12] as [number, number, number], // Deep space black-blue like NASA imagery
  markerColor: [1.0, 0.9, 0.6] as [number, number, number], // Bright warm city lights
  glowColor: [0.3, 0.5, 0.9] as [number, number, number], // Realistic atmospheric glow
  // Major cities with realistic light intensity based on population/infrastructure
  markers: [
    // North America
    { location: [40.7128, -74.006] as [number, number], size: 0.15 }, // New York
    { location: [34.0522, -118.2437] as [number, number], size: 0.12 }, // Los Angeles
    { location: [41.8781, -87.6298] as [number, number], size: 0.10 }, // Chicago
    { location: [29.7604, -95.3698] as [number, number], size: 0.08 }, // Houston
    { location: [39.7392, -104.9903] as [number, number], size: 0.06 }, // Denver
    { location: [37.7749, -122.4194] as [number, number], size: 0.11 }, // San Francisco
    { location: [47.6062, -122.3321] as [number, number], size: 0.07 }, // Seattle
    { location: [25.7617, -80.1918] as [number, number], size: 0.08 }, // Miami
    { location: [32.7767, -96.7970] as [number, number], size: 0.08 }, // Dallas
    { location: [33.4484, -112.0740] as [number, number], size: 0.07 }, // Phoenix
    
    // Europe
    { location: [51.5074, -0.1278] as [number, number], size: 0.13 }, // London
    { location: [48.8566, 2.3522] as [number, number], size: 0.12 }, // Paris
    { location: [52.5200, 13.4050] as [number, number], size: 0.10 }, // Berlin
    { location: [41.9028, 12.4964] as [number, number], size: 0.09 }, // Rome
    { location: [40.4168, -3.7038] as [number, number], size: 0.10 }, // Madrid
    { location: [55.7558, 37.6176] as [number, number], size: 0.14 }, // Moscow
    { location: [59.9311, 30.3609] as [number, number], size: 0.08 }, // St. Petersburg
    { location: [50.1109, 8.6821] as [number, number], size: 0.07 }, // Frankfurt
    { location: [52.3676, 4.9041] as [number, number], size: 0.08 }, // Amsterdam
    { location: [55.6761, 12.5683] as [number, number], size: 0.06 }, // Copenhagen
    
    // Asia
    { location: [35.6762, 139.6503] as [number, number], size: 0.16 }, // Tokyo - Largest metropolitan area
    { location: [39.9042, 116.4074] as [number, number], size: 0.15 }, // Beijing
    { location: [31.2304, 121.4737] as [number, number], size: 0.14 }, // Shanghai
    { location: [22.3193, 114.1694] as [number, number], size: 0.10 }, // Hong Kong
    { location: [37.5665, 126.9780] as [number, number], size: 0.12 }, // Seoul
    { location: [1.3521, 103.8198] as [number, number], size: 0.09 }, // Singapore
    { location: [28.6139, 77.2090] as [number, number], size: 0.13 }, // Delhi
    { location: [19.076, 72.8777] as [number, number], size: 0.12 }, // Mumbai
    { location: [13.0827, 80.2707] as [number, number], size: 0.08 }, // Chennai
    { location: [12.9716, 77.5946] as [number, number], size: 0.09 }, // Bangalore
    
    // Middle East
    { location: [25.2048, 55.2708] as [number, number], size: 0.09 }, // Dubai
    { location: [29.3117, 47.4818] as [number, number], size: 0.07 }, // Kuwait City
    { location: [24.7136, 46.6753] as [number, number], size: 0.08 }, // Riyadh
    { location: [32.0853, 34.7818] as [number, number], size: 0.07 }, // Tel Aviv
    { location: [35.6892, 51.3890] as [number, number], size: 0.10 }, // Tehran
    
    // Africa
    { location: [30.0444, 31.2357] as [number, number], size: 0.10 }, // Cairo
    { location: [-26.2041, 28.0473] as [number, number], size: 0.09 }, // Johannesburg
    { location: [6.5244, 3.3792] as [number, number], size: 0.10 }, // Lagos
    { location: [-33.9249, 18.4241] as [number, number], size: 0.07 }, // Cape Town
    { location: [-1.2921, 36.8219] as [number, number], size: 0.06 }, // Nairobi
    
    // South America
    { location: [-23.5505, -46.6333] as [number, number], size: 0.13 }, // São Paulo
    { location: [-22.9068, -43.1729] as [number, number], size: 0.11 }, // Rio de Janeiro
    { location: [-34.6037, -58.3816] as [number, number], size: 0.11 }, // Buenos Aires
    { location: [4.7110, -74.0721] as [number, number], size: 0.08 }, // Bogotá
    { location: [-12.0464, -77.0428] as [number, number], size: 0.08 }, // Lima
    { location: [-33.4489, -70.6693] as [number, number], size: 0.07 }, // Santiago
    
    // Oceania
    { location: [-33.8688, 151.2093] as [number, number], size: 0.09 }, // Sydney
    { location: [-37.8136, 144.9631] as [number, number], size: 0.08 }, // Melbourne
    { location: [-27.4698, 153.0251] as [number, number], size: 0.06 }, // Brisbane
    { location: [-31.9505, 115.8605] as [number, number], size: 0.05 }, // Perth
    { location: [-36.8485, 174.7633] as [number, number], size: 0.05 }, // Auckland
  ],
};

export interface GlobeProps {
  className?: string;
  config?: typeof REALISTIC_GLOBE_CONFIG;
}

export default function Globe({ className, config = REALISTIC_GLOBE_CONFIG }: GlobeProps) {
  let phi = 0;
  let width = 0;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointerInteracting = useRef(null);
  const pointerInteractionMovement = useRef(0);
  const [r, g, b] = config.baseColor || REALISTIC_GLOBE_CONFIG.baseColor;

  const updatePointerInteraction = (value: any) => {
    pointerInteracting.current = value;
    if (canvasRef.current) {
      canvasRef.current.style.cursor = value ? "grabbing" : "grab";
    }
  };

  const updateMovement = (clientX: any) => {
    if (pointerInteracting.current !== null) {
      const delta = clientX - pointerInteracting.current;
      pointerInteractionMovement.current = delta;
      phi += delta * 0.01;
    }
  };

  const onRender = useCallback(
    (state: Record<string, any>) => {
      // Smooth auto-rotation when not interacting (like ISS orbital view)
      if (!pointerInteracting.current) {
        phi += 0.002;
      }
      
      state.phi = phi + r;
      state.width = width * 2;
      state.height = width * 2;
      
      // Realistic city lights with subtle variations like NASA satellite imagery
      const time = Date.now() * 0.0008;
      const lightVariation = Math.sin(time) * 0.03;
      
      state.markerColor = [
        1.0,
        0.9 + lightVariation,
        0.6 + lightVariation * 0.5
      ];
      
      // Dynamic atmospheric glow like real Earth from space
      state.glowColor = [
        0.3 + Math.sin(time * 0.3) * 0.05,
        0.5 + Math.sin(time * 0.4) * 0.08,
        0.9 + Math.sin(time * 0.2) * 0.05
      ];
      
      // Enhance the space-like deep contrast
      state.dark = 0.2 + Math.sin(time * 0.1) * 0.02;
    },
    [r]
  );

  const onResize = () => {
    if (canvasRef.current) {
      width = canvasRef.current.offsetWidth;
    }
  };

  useEffect(() => {
    window.addEventListener("resize", onResize);
    onResize();

    if (!canvasRef.current) return;

    const globe = createGlobe(canvasRef.current, {
      ...config,
      width: width * 2,
      height: width * 2,
      onRender,
    });

    // Smooth fade-in effect
    setTimeout(() => {
      if (canvasRef.current) {
        canvasRef.current.style.opacity = "1";
      }
    }, 100);
    
    return () => globe.destroy();
  }, [config, onRender]);

  return (
    <div
      className={cn(
        "absolute inset-0 mx-auto aspect-[1/1] w-full max-w-[600px]",
        className
      )}
    >
      <canvas
        className={cn(
          "h-full w-full opacity-0 transition-opacity duration-1500 [contain:layout_style_size]",
          "filter drop-shadow-[0_0_50px_rgba(59,130,246,0.3)] brightness-110 contrast-125", // NASA-like space glow
          "hover:drop-shadow-[0_0_80px_rgba(59,130,246,0.4)] transition-all duration-700"
        )}
        ref={canvasRef}
        onPointerDown={(e) =>
          updatePointerInteraction(
            e.clientX - pointerInteractionMovement.current
          )
        }
        onPointerUp={() => updatePointerInteraction(null)}
        onPointerOut={() => updatePointerInteraction(null)}
        onMouseMove={(e) => updateMovement(e.clientX)}
        onTouchMove={(e) =>
          e.touches[0] && updateMovement(e.touches[0].clientX)
        }
      />
    </div>
  );
}

export { Globe };