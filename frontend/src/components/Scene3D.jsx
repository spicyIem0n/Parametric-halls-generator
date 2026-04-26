import React, { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Sky } from '@react-three/drei';

// Funkcja pomocnicza do mapowania typów na kategorie widoczności
const getCategory = (type) => {
  if (type.includes('column') || type.includes('truss') || type.includes('purlin') || type.includes('girt')) return 'structure';
  if (type.includes('dock') || type.includes('gate')) return 'cladding'; // Doki podpinamy pod widoczność obudowy
  if (type.includes('sandwich_panel')) return 'cladding';
  if (type.includes('roof')) return 'roof';
  if (type.includes('floor') || type.includes('foundation') || type.includes('plinth')) return 'foundation';
  return 'other';
};

const HallElement = ({ type, position, rotation, scale, visibilities, planarOpacity }) => {
  const category = getCategory(type);
  
  // Jeśli kategoria jest odznaczona w UI, nie renderujemy elementu
  if (!visibilities[category]) return null;

  let color = '#718096'; 
  let roughness = 0.6;
  let metalness = 0.4;
  let opacity = 1;
  let transparent = false;

  // Mapa materiałów
  if (type === 'column') {
    color = '#334155'; 
    if (type === 'dock_door') { color = '#475569'; roughness = 0.8; metalness = 0.2; }
    else if (type === 'gate_door') { color = '#f97316'; roughness = 0.5; metalness = 0.5; } // Pomarańczowa brama kurierska
    else if (type === 'dock_shelter') { color = '#1e3a8a'; roughness = 0.9; metalness = 0.1; } // Granatowy fartuch
  } else if (type.startsWith('truss_')) {
    color = '#1e293b'; 
  } else if (type === 'purlin' || type === 'purlin_strut' || type === 'girt') {
    color = '#64748b'; 
  } else if (type === 'drainage_inlet') {
    color = '#0ea5e9'; roughness = 0.2; metalness = 0.8;
  } else if (type === 'foundation') {
    color = '#94a3b8'; roughness = 0.9; metalness = 0.0;
  } else if (type === 'plinth') {
    color = '#64748b'; roughness = 0.8; metalness = 0.0;
  } 

  // --- LOGIKA TRANSPARENTNOŚCI DLA PŁASZCZYZN ---
  const isPlanar = ['sandwich_panel', 'sandwich_panel_v', 'roof_panel', 'floor_slab', 'floor_base_lean_concrete', 'floor_base_cement_stabilized'].includes(type);
  
  if (isPlanar) {
    if (type.includes('sandwich')) color = '#f8fafc';
    if (type.includes('roof')) color = '#e2e8f0';
    if (type === 'floor_slab') color = '#cbd5e1';
    
    transparent = true;
    opacity = planarOpacity;
  }

  return (
    <mesh position={position} rotation={rotation} scale={scale}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color={color} roughness={roughness} metalness={metalness} transparent={transparent} opacity={opacity} />
    </mesh>
  );
};

const Scene3D = ({ components }) => {
  // Stany dla naszego nowego widgetu
  const [visibilities, setVisibilities] = useState({
    structure: true,
    cladding: true,
    roof: true,
    foundation: true
  });
  const [planarOpacity, setPlanarOpacity] = useState(0.4);

  const toggleVisibility = (cat) => {
    setVisibilities(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  return (
    <div className="relative flex-1 h-full w-full bg-gray-50">
      
      {/* PŁYWAJĄCY WIDGET KONTROLNY UI */}
      <div className="absolute top-4 right-4 z-10 bg-white p-4 rounded-lg shadow-lg border border-gray-200 w-64">
        <h3 className="font-bold text-gray-700 mb-3 border-b pb-1">Opcje Wizualizacji</h3>
        
        <div className="space-y-2 mb-4 text-sm text-gray-600">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input type="checkbox" checked={visibilities.structure} onChange={() => toggleVisibility('structure')} className="rounded text-blue-500 focus:ring-blue-500"/>
            <span>Konstrukcja Stalowa</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input type="checkbox" checked={visibilities.cladding} onChange={() => toggleVisibility('cladding')} className="rounded text-blue-500 focus:ring-blue-500"/>
            <span>Obudowa (Ściany)</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input type="checkbox" checked={visibilities.roof} onChange={() => toggleVisibility('roof')} className="rounded text-blue-500 focus:ring-blue-500"/>
            <span>Pokrycie Dachu</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input type="checkbox" checked={visibilities.foundation} onChange={() => toggleVisibility('foundation')} className="rounded text-blue-500 focus:ring-blue-500"/>
            <span>Fundamenty i Posadzka</span>
          </label>
        </div>

        <div className="border-t pt-3">
          <label className="text-sm text-gray-600 flex justify-between mb-1">
            <span>Przezroczystość płaszczyzn:</span>
            <span className="font-mono text-xs">{Math.round(planarOpacity * 100)}%</span>
          </label>
          <input 
            type="range" min="0" max="1" step="0.05" 
            value={planarOpacity} 
            onChange={(e) => setPlanarOpacity(parseFloat(e.target.value))}
            className="w-full accent-blue-600"
          />
        </div>
      </div>

      <Canvas camera={{ position: [40, 30, 50], fov: 45 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[20, 40, 20]} intensity={1.2} castShadow />
        <Sky sunPosition={[100, 20, 100]} />
        
        <OrbitControls makeDefault />
        <Grid position={[0, 0, 0]} infiniteGrid fadeDistance={80} sectionColor={'#cbd5e1'} cellColor={'#e2e8f0'} />

        {/* Teren pod poziomem 0 */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]}>
          <planeGeometry args={[300, 300]} />
          <meshStandardMaterial color="#84cc16" transparent opacity={0.15} roughness={1} />
        </mesh>

        <group position={[0, 0, 0]}>
          {components.map((comp, index) => (
            <HallElement key={index} {...comp} visibilities={visibilities} planarOpacity={planarOpacity} />
          ))}
        </group>
      </Canvas>
    </div>
  );
};

export default Scene3D;