import React, { useState, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Sky } from '@react-three/drei';
import * as THREE from 'three';

// Standardowa szerokosc plyty warstwowej sciennej (spoiny co 1.0 m)
const PANEL_MODULE = 1.0;

// Rysuje spoiny miedzy plytami warstwowymi na elewacji (na obu licach panelu).
// - orientation "horizontal": plyty ukladane poziomo -> spoiny POZIOME
//   (linie biegnace wzdluz osi poziomej, rozstawione po wysokosci).
// - orientation "vertical": plyty ukladane pionowo -> spoiny PIONOWE
//   (linie biegnace wzdluz osi pionowej, rozstawione po osi poziomej).
// Panel to boks lokalny 1x1x1 skalowany przez `scale`; os grubosci to
// najmniejsza skladowa scale, os pionowa lica to Y (indeks 1).
const PanelSeams = ({ scale, orientation = 'horizontal', color = '#64748b' }) => {
  const geometry = useMemo(() => {
    const dims = [Math.abs(scale[0]), Math.abs(scale[1]), Math.abs(scale[2])];
    const thickAxis = dims.indexOf(Math.min(...dims));
    const planeAxes = [0, 1, 2].filter((a) => a !== thickAxis);

    // Os pionowa lica = Y (1), jesli lezy w plaszczyznie lica; os pozioma to druga.
    let vertAxis = planeAxes.includes(1) ? 1 : planeAxes[1];
    let horizAxis = planeAxes.find((a) => a !== vertAxis);

    const faceOffset = 0.5; // polowa grubosci w jednostkach lokalnych
    const positions = [];

    const makePoint = (along, at, faceSign) => {
      // `at` — wspolrzedna lokalna na osi rozstawu; `along` — wzdluz drugiej osi
      const p = [0, 0, 0];
      p[thickAxis] = faceSign * faceOffset;
      return { p, along, at };
    };

    // Zwraca lokalne wspolrzedne [-0.5,0.5] spoin rozstawionych co PANEL_MODULE
    // wzdluz osi o rzeczywistej dlugosci realLen (pomija krawedzie).
    const seamCoords = (realLen) => {
      const out = [];
      const n = Math.floor(realLen / PANEL_MODULE + 1e-6);
      for (let i = 1; i <= n; i++) {
        const d = i * PANEL_MODULE;
        if (d >= realLen - 1e-6) break;
        out.push(d / realLen - 0.5);
      }
      return out;
    };

    // Dodaje linie na obu licach; spoiny rozstawione wzdluz `spacingAxis`,
    // a kazda linia biegnie wzdluz `runAxis` (przez cala szerokosc lica).
    const addSeams = (spacingAxis, runAxis) => {
      const coords = seamCoords(dims[spacingAxis]);
      for (const faceSign of [1, -1]) {
        for (const c of coords) {
          const a = [0, 0, 0];
          const b = [0, 0, 0];
          a[thickAxis] = faceSign * faceOffset;
          b[thickAxis] = faceSign * faceOffset;
          a[spacingAxis] = c;
          b[spacingAxis] = c;
          a[runAxis] = -0.5;
          b[runAxis] = 0.5;
          positions.push(...a, ...b);
        }
      }
    };

    if (orientation === 'vertical') {
      // spoiny pionowe: rozstawione po osi poziomej, linie biegna pionowo (Y)
      addSeams(horizAxis, vertAxis);
    } else {
      // spoiny poziome: rozstawione po wysokosci (Y), linie biegna poziomo
      addSeams(vertAxis, horizAxis);
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    return geo;
  }, [scale, orientation]);

  if (!geometry.attributes.position || geometry.attributes.position.count === 0) {
    return null;
  }

  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={0.55} />
    </lineSegments>
  );
};

// Funkcja pomocnicza do mapowania typów na kategorie widoczności
const getCategory = (type) => {
  if (type.includes('column') || type.includes('truss') || type.includes('purlin') || type.includes('girt') || type.includes('trimmer')) return 'structure';
  if (type.includes('fire_wall') || type.includes('fire_strip')) return 'structure';
  if (type.includes('bracing')) return 'structure';
  if (type.includes('tech_room')) return 'structure';
  if (type.includes('office')) return 'structure';
  if (type.includes('mezzanine')) return 'structure';
  if (type.includes('reserve')) return 'roof';
  if (type === 'skylight' || type === 'smoke_vent' || type === 'light_strip') return 'roof';
  if (type.includes('dock') || type.includes('gate')) return 'cladding';
  if (type.includes('cladding_rail')) return 'structure';
  if (type.includes('sandwich_panel')) return 'cladding';
  if (type.includes('roof')) return 'roof';
  if (type.includes('floor') || type.includes('foundation') || type.includes('plinth')) return 'foundation';
  return 'other';
};

const HallElement = ({ type, position, rotation, scale, meta, visibilities, planarOpacity }) => {
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
  } else if (type === 'trimmer') {
    color = '#7c3aed'; roughness = 0.5; metalness = 0.5; // Fioletowy — wymiany
  } else if (type === 'drainage_inlet') {
    color = '#0ea5e9'; roughness = 0.2; metalness = 0.8;
  } else if (type === 'foundation') {
    color = '#94a3b8'; roughness = 0.9; metalness = 0.0;
  } else if (type === 'plinth') {
    color = '#64748b'; roughness = 0.8; metalness = 0.0;
  } else if (type === 'fire_wall') {
    color = '#b91c1c'; roughness = 0.9; metalness = 0.0; // Ciemnoczerwony ŚOP
  } else if (type === 'fire_strip_roof') {
    color = '#fbbf24'; roughness = 0.7; metalness = 0.1; // Żółty pas niepalny
  } else if (type === 'bracing' || type === 'bracing_roof') {
    color = '#16a34a'; roughness = 0.4; metalness = 0.6; // Zielony — stężenia
  } else if (type === 'tech_room_wall') {
    color = '#7f1d1d'; roughness = 0.9; metalness = 0.0; // Burgundowy — pomieszczenia techniczne
  } else if (type === 'tech_room_slab') {
    color = '#6b2121'; roughness = 0.9; metalness = 0.0;
  } else if (type === 'tech_room_door') {
    color = '#d97706'; roughness = 0.5; metalness = 0.3; // Złoty — drzwi EI
  } else if (type === 'office_column') {
    color = '#475569'; roughness = 0.5; metalness = 0.5;
  } else if (type === 'office_slab' || type === 'office_roof') {
    color = '#e2e8f0'; roughness = 0.8; metalness = 0.1;
  } else if (type === 'office_wall') {
    color = '#fef3c7'; roughness = 0.7; metalness = 0.1; // Kremowy
  } else if (type === 'office_fire_wall') {
    color = '#b91c1c'; roughness = 0.9; metalness = 0.0; // Czerwony ppoż
  } else if (type === 'office_stairs') {
    color = '#6b7280'; roughness = 0.6; metalness = 0.3;
  } else if (type === 'mezzanine_column') {
    color = '#64748b'; roughness = 0.5; metalness = 0.4;
  } else if (type === 'mezzanine_fire_wall') {
    color = '#be185d'; roughness = 0.9; metalness = 0.0; // Różowoczerwony
  } else if (type === 'mezzanine_balustrade') {
    color = '#a3a3a3'; roughness = 0.4; metalness = 0.7;
  } else if (type === 'mezzanine_stairs') {
    color = '#6b7280'; roughness = 0.6; metalness = 0.3;
  } else if (type === 'reserve_purlin_doubled') {
    color = '#ea580c'; roughness = 0.4; metalness = 0.6; // Pomarańczowy — zdublowane płatwie
  } else if (type === 'reserve_truss_marker') {
    color = '#f97316'; roughness = 0.3; metalness = 0.7; // Jasny pomarańcz — dźwigary w strefie
  } else if (type === 'reserve_zone_marker') {
  } else if (type === 'skylight') {
    color = '#38bdf8'; roughness = 0.2; metalness = 0.1; transparent = true; opacity = 0.7;
  } else if (type === 'smoke_vent') {
    color = '#6b7280'; roughness = 0.3; metalness = 0.7;
  } else if (type === 'light_strip') {
    color = '#67e8f9'; roughness = 0.1; metalness = 0.1; transparent = true; opacity = 0.6;
    color = '#fbbf24'; roughness = 0.5; metalness = 0.2; // Żółty marker strefy
    transparent = true; opacity = 0.3;
  } 

  // --- LOGIKA TRANSPARENTNOŚCI DLA PŁASZCZYZN ---
  const isPlanar = ['sandwich_panel', 'sandwich_panel_v', 'roof_panel', 'floor_slab', 'floor_base_lean_concrete', 'floor_base_cement_stabilized', 'office_slab', 'office_roof', 'mezzanine_slab'].includes(type);
  
  if (isPlanar) {
    if (type.includes('sandwich')) color = '#f8fafc';
    if (type.includes('roof')) color = '#e2e8f0';
    if (type === 'floor_slab') color = '#cbd5e1';
    
    transparent = true;
    opacity = planarOpacity;
  }

  // --- NADPISANIE KOLORU DLA ELEMENTÓW Z WYMAGANIAMI PPOŻ ---
  if (meta && meta.fire_rating && meta.fire_rating !== 'none') {
    // Elementy z wymaganą ochroną ppoż — podświetlenie na pomarańczowo/czerwono
    const rating = meta.fire_rating;
    if (rating.includes('240') || rating.includes('120')) {
      color = '#dc2626'; // Czerwony — wysokie wymagania (R120+)
    } else if (rating.includes('60')) {
      color = '#ea580c'; // Pomarańczowy — średnie wymagania (R60)
    } else {
      color = '#f59e0b'; // Żółty — niskie wymagania (R15/R30)
    }
    roughness = 0.4;
    metalness = 0.6;
  }

  // Spoiny miedzy plytami warstwowymi TYLKO na elewacji (obudowa scienna).
  // Dach pozostaje bez podzialow. Kierunek spoin wg orientacji montazu.
  const showSeams = type === 'sandwich_panel' || type === 'sandwich_panel_v';
  const seamOrientation =
    (meta && meta.cladding_orientation) ||
    (type === 'sandwich_panel_v' ? 'vertical' : 'horizontal');

  return (
    <mesh position={position} rotation={rotation} scale={scale}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color={color} roughness={roughness} metalness={metalness} transparent={transparent} opacity={opacity} />
      {showSeams && <PanelSeams scale={scale} orientation={seamOrientation} color="#64748b" />}
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
