import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Sky } from '@react-three/drei';

const HallElement = ({ type, position, rotation, scale }) => {
  let color = '#718096'; 
  let roughness = 0.6;
  let metalness = 0.4;
  let opacity = 1;
  let transparent = false;

  // Mapa materiałów
  if (type === 'column') {
    color = '#334155'; 
  } else if (type.startsWith('truss_')) {
    color = '#1e293b'; // Ciemna stal kratownicy
  } else if (type === 'purlin') {
    color = '#64748b'; // Ocynkowane płatwie
  //... wewnątrz HallElement
  } else if (type === 'drainage_inlet') {
    color = '#0ea5e9'; // Jaskrawy błękit dla wpustów podciśnieniowych
    roughness = 0.2; metalness = 0.8;
  } else if (type === 'purlin_strut') {
    color = '#94a3b8'; // Ocynkowane stalowe słupki dystansowe płatwi
  } else if (type === 'sandwich_panel' || type === 'sandwich_panel_v') {
//...
  } else if (type === 'roof_panel') {
    color = '#e2e8f0'; // Jasne poszycie dachu
    roughness = 0.2;
    metalness = 0.1;
  } else if (type === 'foundation') {
    color = '#94a3b8'; 
    roughness = 0.9; metalness = 0.0;
  } else if (type === 'plinth') {
    color = '#64748b'; // Ciemniejszy beton architektoniczny podwaliny
    roughness = 0.8; metalness = 0.0;
  } else if (type === 'floor_slab') {
    color = '#cbd5e1'; 
    roughness = 0.5; metalness = 0.1;
  } else if (type === 'floor_base_lean_concrete') {
    color = '#94a3b8'; roughness = 0.9; metalness = 0.0;
  } else if (type === 'floor_base_cement_stabilized') {
    color = '#a8a29e'; roughness = 1.0; metalness = 0.0;
  } else if (type === 'sandwich_panel' || type === 'sandwich_panel_v') {
    color = '#f8fafc'; 
    roughness = 0.3; metalness = 0.2;
    transparent = true; opacity = 0.75; // Wyższa przezroczystość, by widzieć kratownice
  } else if (type === 'girt') {
    color = '#64748b';
  }

  return (
    <mesh position={position} rotation={rotation} scale={scale}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color={color} roughness={roughness} metalness={metalness} transparent={transparent} opacity={opacity} />
    </mesh>
  );
};

const Scene3D = ({ components }) => {
  return (
    <div className="flex-1 h-full w-full bg-gray-50">
      <Canvas camera={{ position: [35, 25, 45], fov: 45 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[20, 40, 20]} intensity={1.2} castShadow />
        <Sky sunPosition={[100, 20, 100]} />
        
        <OrbitControls makeDefault />
        <Grid position={[0, 0, 0]} infiniteGrid fadeDistance={80} sectionColor={'#cbd5e1'} cellColor={'#e2e8f0'} />

        {/* Realistyczny, transparentny teren poniżej poziomu 0.00 */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]}>
          <planeGeometry args={[300, 300]} />
          <meshStandardMaterial color="#84cc16" transparent opacity={0.15} roughness={1} />
        </mesh>

        <group position={[0, 0, 0]}>
          {components.map((comp, index) => (
            <HallElement key={index} {...comp} />
          ))}
        </group>
      </Canvas>
    </div>
  );
};

export default Scene3D;