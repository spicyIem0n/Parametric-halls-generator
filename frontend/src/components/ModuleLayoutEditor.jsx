import React, { useRef, useState, useEffect, useCallback } from 'react';

const SNAP_THRESHOLD = 2.0; // metry - prog przyciagania (wiekszy = latwiejsze dosnappowanie)
const GRID_STEP = 6; // metry - siatka pomocnicza
const MIN_ZOOM = 0.3;
const MAX_ZOOM = 3.0;

// Kolory dla modulow
const MODULE_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1',
];

const ModuleLayoutEditor = ({ modules, setModules, connections, setConnections, selectedModuleId, setSelectedModuleId }) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1.0);
  const [dragging, setDragging] = useState(null); // { moduleIdx, startMouse, startPos }
  const [panning, setPanning] = useState(null); // { startMouse, startOffset }
  const [canvasSize, setCanvasSize] = useState({ w: 600, h: 400 });
  const [hoveredConnection, setHoveredConnection] = useState(null);
  const [snapLines, setSnapLines] = useState([]); // [{axis:'x'|'z', value:number}]

  // Resize observer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setCanvasSize({ w: width, h: height });
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  // Przeliczanie wspolrzednych
  const worldToScreen = useCallback((wx, wz) => {
    const sx = canvasSize.w / 2 + (wx + viewOffset.x) * zoom;
    const sy = canvasSize.h / 2 + (wz + viewOffset.y) * zoom;
    return [sx, sy];
  }, [canvasSize, viewOffset, zoom]);

  const screenToWorld = useCallback((sx, sy) => {
    const wx = (sx - canvasSize.w / 2) / zoom - viewOffset.x;
    const wz = (sy - canvasSize.h / 2) / zoom - viewOffset.y;
    return [wx, wz];
  }, [canvasSize, viewOffset, zoom]);

  // Efektywne wymiary modulu na rzucie 2D (zamienione przy frame_orientation=90)
  const getEffectiveDims = useCallback((mod) => {
    if ((mod.frame_orientation || 0) === 90) {
      return { w: mod.length, l: mod.width };
    }
    return { w: mod.width, l: mod.length };
  }, []);

  // Snap logic
  const snapPosition = useCallback((moduleIdx, newX, newZ) => {
    const mod = modules[moduleIdx];
    const { w: modW, l: modL } = getEffectiveDims(mod);

    // Krawedzie przesuwanego modulu
    const edges = {
      left: newX - modW / 2,
      right: newX + modW / 2,
      top: newZ - modL / 2,
      bottom: newZ + modL / 2,
    };

    let snappedX = newX;
    let snappedZ = newZ;
    let bestDx = SNAP_THRESHOLD;
    let bestDz = SNAP_THRESHOLD;

    for (let i = 0; i < modules.length; i++) {
      if (i === moduleIdx) continue;
      const other = modules[i];
      const oX = other.position_x;
      const oZ = other.position_z;
      const { w: oW, l: oL } = getEffectiveDims(other);
      const oEdges = {
        left: oX - oW / 2,
        right: oX + oW / 2,
        top: oZ - oL / 2,
        bottom: oZ + oL / 2,
      };

      // Snap X: lewa do prawej, prawa do lewej, lewa do lewej, prawa do prawej
      const xPairs = [
        [edges.left, oEdges.right],
        [edges.right, oEdges.left],
        [edges.left, oEdges.left],
        [edges.right, oEdges.right],
      ];
      for (const [myEdge, otherEdge] of xPairs) {
        const d = Math.abs(myEdge - otherEdge);
        if (d < bestDx) {
          bestDx = d;
          snappedX = newX + (otherEdge - myEdge);
        }
      }

      // Snap Z: gora do dolu, dol do gory, gora do gory, dol do dolu
      const zPairs = [
        [edges.top, oEdges.bottom],
        [edges.bottom, oEdges.top],
        [edges.top, oEdges.top],
        [edges.bottom, oEdges.bottom],
      ];
      for (const [myEdge, otherEdge] of zPairs) {
        const d = Math.abs(myEdge - otherEdge);
        if (d < bestDz) {
          bestDz = d;
          snappedZ = newZ + (otherEdge - myEdge);
        }
      }
    }

    // Dodatkowy snap: wyrownanie srodkow modulow (osia X i Z)
    for (let i = 0; i < modules.length; i++) {
      if (i === moduleIdx) continue;
      const other = modules[i];
      // Snap center X
      if (Math.abs(newX - other.position_x) < bestDx) {
        bestDx = Math.abs(newX - other.position_x);
        snappedX = other.position_x;
      }
      // Snap center Z
      if (Math.abs(newZ - other.position_z) < bestDz) {
        bestDz = Math.abs(newZ - other.position_z);
        snappedZ = other.position_z;
      }
    }

    // Snap do osi globalnych (X=0, Z=0)
    if (Math.abs(snappedX) < SNAP_THRESHOLD * 0.7) snappedX = 0;
    if (Math.abs(snappedZ) < SNAP_THRESHOLD * 0.7) snappedZ = 0;

    return [snappedX, snappedZ];
  }, [modules, getEffectiveDims]);

  // Wykrywanie stykow miedzy modulami
  const detectConnections = useCallback((mods) => {
    const conns = [];
    const tolerance = 0.1;
    for (let i = 0; i < mods.length; i++) {
      for (let j = i + 1; j < mods.length; j++) {
        const a = mods[i], b = mods[j];
        const aD = getEffectiveDims(a), bD = getEffectiveDims(b);
        const aL = a.position_x - aD.w / 2, aR = a.position_x + aD.w / 2;
        const aT = a.position_z - aD.l / 2, aB = a.position_z + aD.l / 2;
        const bL = b.position_x - bD.w / 2, bR = b.position_x + bD.w / 2;
        const bT = b.position_z - bD.l / 2, bB = b.position_z + bD.l / 2;

        // Sprawdz kazda pare krawedzi
        // A prawa = B lewa (styk w X)
        if (Math.abs(aR - bL) < tolerance) {
          const overlapStart = Math.max(aT, bT);
          const overlapEnd = Math.min(aB, bB);
          if (overlapEnd - overlapStart > tolerance) {
            conns.push({ moduleA: i, moduleB: j, side: 'x', position: aR, overlap: [overlapStart, overlapEnd] });
          }
        }
        // A lewa = B prawa
        if (Math.abs(aL - bR) < tolerance) {
          const overlapStart = Math.max(aT, bT);
          const overlapEnd = Math.min(aB, bB);
          if (overlapEnd - overlapStart > tolerance) {
            conns.push({ moduleA: j, moduleB: i, side: 'x', position: aL, overlap: [overlapStart, overlapEnd] });
          }
        }
        // A dol = B gora (styk w Z)
        if (Math.abs(aB - bT) < tolerance) {
          const overlapStart = Math.max(aL, bL);
          const overlapEnd = Math.min(aR, bR);
          if (overlapEnd - overlapStart > tolerance) {
            conns.push({ moduleA: i, moduleB: j, side: 'z', position: aB, overlap: [overlapStart, overlapEnd] });
          }
        }
        // A gora = B dol
        if (Math.abs(aT - bB) < tolerance) {
          const overlapStart = Math.max(aL, bL);
          const overlapEnd = Math.min(aR, bR);
          if (overlapEnd - overlapStart > tolerance) {
            conns.push({ moduleA: j, moduleB: i, side: 'z', position: aT, overlap: [overlapStart, overlapEnd] });
          }
        }
      }
    }
    return conns;
  }, [getEffectiveDims]);

  // Rysowanie
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvasSize.w;
    const H = canvasSize.h;
    canvas.width = W * window.devicePixelRatio;
    canvas.height = H * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Tlo
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, W, H);

    // Siatka
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 0.5;
    const gridWorldStep = GRID_STEP;
    const [originSx, originSy] = worldToScreen(0, 0);

    // Pionowe linie siatki
    const startWx = Math.floor((-viewOffset.x - W / 2 / zoom) / gridWorldStep) * gridWorldStep;
    const endWx = Math.ceil((-viewOffset.x + W / 2 / zoom) / gridWorldStep) * gridWorldStep;
    for (let wx = startWx; wx <= endWx; wx += gridWorldStep) {
      const [sx] = worldToScreen(wx, 0);
      ctx.beginPath();
      ctx.moveTo(sx, 0);
      ctx.lineTo(sx, H);
      ctx.stroke();
    }
    // Poziome
    const startWz = Math.floor((-viewOffset.y - H / 2 / zoom) / gridWorldStep) * gridWorldStep;
    const endWz = Math.ceil((-viewOffset.y + H / 2 / zoom) / gridWorldStep) * gridWorldStep;
    for (let wz = startWz; wz <= endWz; wz += gridWorldStep) {
      const [, sy] = worldToScreen(0, wz);
      ctx.beginPath();
      ctx.moveTo(0, sy);
      ctx.lineTo(W, sy);
      ctx.stroke();
    }

    // Osie
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(originSx, 0); ctx.lineTo(originSx, H);
    ctx.moveTo(0, originSy); ctx.lineTo(W, originSy);
    ctx.stroke();

    // Moduly
    modules.forEach((mod, idx) => {
      const x = mod.position_x;
      const z = mod.position_z;
      const { w, l } = getEffectiveDims(mod);
      const [sx, sy] = worldToScreen(x - w / 2, z - l / 2);
      const sw = w * zoom;
      const sl = l * zoom;
      const color = MODULE_COLORS[idx % MODULE_COLORS.length];
      const isSelected = mod.block_id === selectedModuleId;

      // Prostokat
      ctx.fillStyle = color + '20';
      ctx.fillRect(sx, sy, sw, sl);
      ctx.strokeStyle = isSelected ? '#1d4ed8' : color;
      ctx.lineWidth = isSelected ? 2.5 : 1.5;
      ctx.strokeRect(sx, sy, sw, sl);

      // Znacznik orientacji ram (linie przerywane)
      // orient=0: ramy biegna wzdluz X, powtarzane w Z -> linie poziome (dziela l)
      // orient=90: ramy biegna wzdluz Z, powtarzane w X -> linie pionowe (dziela w)
      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = color + '80';
      ctx.lineWidth = 1;
      const orientation = mod.frame_orientation || 0;
      const spacing = mod.bay_spacing || 6;
      if (orientation === 0) {
        // Powtarzalnosc wzdluz Z (efektywne l) -> linie poziome
        const numBays = Math.max(1, Math.round(l / spacing));
        for (let b = 1; b < numBays; b++) {
          const bz = z - l / 2 + b * (l / numBays);
          const [, bsy] = worldToScreen(x, bz);
          ctx.beginPath();
          ctx.moveTo(sx, bsy);
          ctx.lineTo(sx + sw, bsy);
          ctx.stroke();
        }
      } else {
        // Powtarzalnosc wzdluz X (efektywne w) -> linie pionowe
        const numBays = Math.max(1, Math.round(w / spacing));
        for (let b = 1; b < numBays; b++) {
          const bx = x - w / 2 + b * (w / numBays);
          const [bsx] = worldToScreen(bx, z);
          ctx.beginPath();
          ctx.moveTo(bsx, sy);
          ctx.lineTo(bsx, sy + sl);
          ctx.stroke();
        }
      }
      ctx.restore();

      // Etykieta
      const fontSize = Math.max(8, Math.min(14, 12 * zoom));
      ctx.fillStyle = '#1e293b';
      ctx.font = `bold ${fontSize}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(mod.block_id, sx + sw / 2, sy + sl / 2 - fontSize * 0.6);
      ctx.font = `${fontSize * 0.75}px sans-serif`;
      ctx.fillStyle = '#475569';
      ctx.fillText(`${mod.width} x ${mod.length} m`, sx + sw / 2, sy + sl / 2 + fontSize * 0.5);
      ctx.fillText(`h=${mod.clear_height}m | ramy: ${orientation === 0 ? "wzdł. szer." : "wzdł. dł. (90°)"}`, sx + sw / 2, sy + sl / 2 + fontSize * 1.3);
    });

    // Polaczenia (styki)
    const detectedConns = detectConnections(modules);
    detectedConns.forEach((conn, ci) => {
      const existingConn = connections.find(c =>
        (c.moduleA === conn.moduleA && c.moduleB === conn.moduleB) ||
        (c.moduleA === conn.moduleB && c.moduleB === conn.moduleA)
      );
      const connType = existingConn?.type || 'expansion_joint';
      const isHovered = hoveredConnection === ci;

      ctx.save();
      ctx.lineWidth = isHovered ? 4 : 2.5;
      if (connType === 'fire_wall') {
        ctx.strokeStyle = '#ef4444';
        ctx.setLineDash([6, 3]);
      } else if (connType === 'internal_wall') {
        ctx.strokeStyle = '#f59e0b';
        ctx.setLineDash([4, 4]);
      } else if (connType === 'none') {
        ctx.strokeStyle = '#10b981';
        ctx.setLineDash([2, 6]);
      } else {
        ctx.strokeStyle = '#6366f1';
        ctx.setLineDash([8, 4]);
      }

      if (conn.side === 'x') {
        const [sx, sy1] = worldToScreen(conn.position, conn.overlap[0]);
        const [, sy2] = worldToScreen(conn.position, conn.overlap[1]);
        ctx.beginPath();
        ctx.moveTo(sx, sy1);
        ctx.lineTo(sx, sy2);
        ctx.stroke();
      } else {
        const [sx1, sy] = worldToScreen(conn.overlap[0], conn.position);
        const [sx2] = worldToScreen(conn.overlap[1], conn.position);
        ctx.beginPath();
        ctx.moveTo(sx1, sy);
        ctx.lineTo(sx2, sy);
        ctx.stroke();
      }
      ctx.restore();
    });

    // Snap lines (linie prowadzace)
    if (snapLines.length > 0) {
      ctx.save();
      ctx.strokeStyle = '#f43f5e';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 4]);
      for (const sl of snapLines) {
        if (sl.axis === 'x') {
          const [sx] = worldToScreen(sl.value, 0);
          ctx.beginPath();
          ctx.moveTo(sx, 0);
          ctx.lineTo(sx, H);
          ctx.stroke();
        } else {
          const [, sy] = worldToScreen(0, sl.value);
          ctx.beginPath();
          ctx.moveTo(0, sy);
          ctx.lineTo(W, sy);
          ctx.stroke();
        }
      }
      ctx.restore();
    }

    // Legenda
    ctx.fillStyle = '#64748b';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`Zoom: ${(zoom * 100).toFixed(0)}% | Siatka: ${GRID_STEP}m | Snap: ${SNAP_THRESHOLD}m`, 8, H - 8);

  }, [modules, canvasSize, viewOffset, zoom, selectedModuleId, connections, hoveredConnection, snapLines, worldToScreen, detectConnections, getEffectiveDims]);

  // Mouse handlers
  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const [wx, wz] = screenToWorld(mx, my);

    // Srodkowy przycisk = pan
    if (e.button === 1) {
      e.preventDefault();
      setPanning({ startMouse: { x: mx, y: my }, startOffset: { ...viewOffset } });
      return;
    }

    // Lewy przycisk = drag modulu lub pan (jesli nie na module)
    if (e.button === 0) {
      // Sprawdz czy kliknieto na modul
      for (let i = modules.length - 1; i >= 0; i--) {
        const mod = modules[i];
        const { w: mW, l: mH } = getEffectiveDims(mod);
        const mL = mod.position_x - mW / 2;
        const mR = mod.position_x + mW / 2;
        const mT = mod.position_z - mH / 2;
        const mB = mod.position_z + mH / 2;
        if (wx >= mL && wx <= mR && wz >= mT && wz <= mB) {
          setDragging({ moduleIdx: i, startMouse: { x: mx, y: my }, startPos: { x: mod.position_x, z: mod.position_z } });
          setSelectedModuleId(mod.block_id);
          return;
        }
      }
      // Klikniecie na styk?
      const detectedConns = detectConnections(modules);
      for (let ci = 0; ci < detectedConns.length; ci++) {
        const conn = detectedConns[ci];
        let hit = false;
        if (conn.side === 'x') {
          hit = Math.abs(wx - conn.position) < 1 && wz >= conn.overlap[0] && wz <= conn.overlap[1];
        } else {
          hit = Math.abs(wz - conn.position) < 1 && wx >= conn.overlap[0] && wx <= conn.overlap[1];
        }
        if (hit) {
          // Cykluj typ polaczenia
          const existing = connections.find(c =>
            (c.moduleA === conn.moduleA && c.moduleB === conn.moduleB) ||
            (c.moduleA === conn.moduleB && c.moduleB === conn.moduleA)
          );
          const types = ['expansion_joint', 'none', 'internal_wall', 'fire_wall'];
          const currentType = existing?.type || 'expansion_joint';
          const nextType = types[(types.indexOf(currentType) + 1) % types.length];

          // Walidacja: prostopadle ramy -> nie mozna "none"
          const modA = modules[conn.moduleA];
          const modB = modules[conn.moduleB];
          const orientA = modA.frame_orientation || 0;
          const orientB = modB.frame_orientation || 0;
          const perpendicular = orientA !== orientB;
          let finalType = nextType;
          if (perpendicular && nextType === 'none') {
            finalType = types[(types.indexOf(nextType) + 1) % types.length]; // skip 'none'
          }

          const newConns = connections.filter(c =>
            !((c.moduleA === conn.moduleA && c.moduleB === conn.moduleB) ||
              (c.moduleA === conn.moduleB && c.moduleB === conn.moduleA))
          );
          newConns.push({ moduleA: conn.moduleA, moduleB: conn.moduleB, type: finalType });
          setConnections(newConns);
          return;
        }
      }

      // Pan
      setPanning({ startMouse: { x: mx, y: my }, startOffset: { ...viewOffset } });
      setSelectedModuleId(null);
    }
  };

  const handleMouseMove = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (panning) {
      const dx = (mx - panning.startMouse.x) / zoom;
      const dy = (my - panning.startMouse.y) / zoom;
      setViewOffset({ x: panning.startOffset.x + dx, y: panning.startOffset.y + dy });
      return;
    }

    if (dragging) {
      const dx = (mx - dragging.startMouse.x) / zoom;
      const dy = (my - dragging.startMouse.y) / zoom;
      let newX = dragging.startPos.x + dx;
      let newZ = dragging.startPos.z + dy;

      // Snap
      const origX = newX, origZ = newZ;
      [newX, newZ] = snapPosition(dragging.moduleIdx, newX, newZ);

      // Snap lines feedback
      const lines = [];
      if (Math.abs(newX - origX) > 0.01) lines.push({ axis: 'x', value: newX });
      if (Math.abs(newZ - origZ) > 0.01) lines.push({ axis: 'z', value: newZ });
      setSnapLines(lines);

      const newModules = [...modules];
      newModules[dragging.moduleIdx] = {
        ...newModules[dragging.moduleIdx],
        position_x: Math.round(newX * 2) / 2, // snap do 0.5m
        position_z: Math.round(newZ * 2) / 2,
      };
      setModules(newModules);
    }
  };

  const handleMouseUp = () => {
    if (dragging) {
      // Po zakonczeniu drag aktualizuj polaczenia
      const newConns = detectConnections(modules);
      // Zachowaj typy istniejacych polaczen
      const mergedConns = newConns.map(nc => {
        const existing = connections.find(c =>
          (c.moduleA === nc.moduleA && c.moduleB === nc.moduleB) ||
          (c.moduleA === nc.moduleB && c.moduleB === nc.moduleA)
        );
        return { ...nc, type: existing?.type || 'expansion_joint' };
      });
      setConnections(mergedConns);
    }
    setDragging(null);
    setPanning(null);
    setSnapLines([]);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(z => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, z * factor)));
  };

  // Fit all
  const handleFitAll = () => {
    if (modules.length === 0) { setViewOffset({ x: 0, y: 0 }); setZoom(1.0); return; }
    let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
    modules.forEach(m => {
      const { w, l } = getEffectiveDims(m);
      minX = Math.min(minX, m.position_x - w / 2);
      maxX = Math.max(maxX, m.position_x + w / 2);
      minZ = Math.min(minZ, m.position_z - l / 2);
      maxZ = Math.max(maxZ, m.position_z + l / 2);
    });
    const worldW = maxX - minX + 20;
    const worldH = maxZ - minZ + 20;
    const newZoom = Math.min(canvasSize.w / worldW, canvasSize.h / worldH, MAX_ZOOM);
    const centerX = (minX + maxX) / 2;
    const centerZ = (minZ + maxZ) / 2;
    setZoom(newZoom);
    setViewOffset({ x: -centerX, y: -centerZ });
  };

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[300px] border border-gray-300 rounded-lg overflow-hidden bg-slate-50">
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', cursor: dragging ? 'grabbing' : 'default' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        onContextMenu={(e) => e.preventDefault()}
      />
      {/* Toolbar */}
      <div className="absolute top-2 right-2 flex flex-col gap-1">
        <button onClick={handleFitAll} className="bg-white border border-gray-300 rounded px-2 py-1 text-[9px] font-bold hover:bg-gray-100 shadow-sm" title="Dopasuj widok">
          ⊞ Fit
        </button>
        <button onClick={() => setZoom(z => Math.min(MAX_ZOOM, z * 1.3))} className="bg-white border border-gray-300 rounded px-2 py-1 text-[9px] font-bold hover:bg-gray-100 shadow-sm">+</button>
        <button onClick={() => setZoom(z => Math.max(MIN_ZOOM, z / 1.3))} className="bg-white border border-gray-300 rounded px-2 py-1 text-[9px] font-bold hover:bg-gray-100 shadow-sm">−</button>
      </div>
      {/* Legenda polaczen */}
      <div className="absolute bottom-2 left-2 bg-white/90 border border-gray-200 rounded p-1.5 text-[8px] leading-relaxed">
        <div><span className="inline-block w-3 h-0.5 bg-indigo-500 mr-1"></span>Dylatacja</div>
        <div><span className="inline-block w-3 h-0.5 bg-green-500 mr-1"></span>Bez ściany</div>
        <div><span className="inline-block w-3 h-0.5 bg-amber-500 mr-1"></span>Ściana wewnętrzna</div>
        <div><span className="inline-block w-3 h-0.5 bg-red-500 mr-1"></span>Ściana PPOŻ</div>
        <div className="mt-0.5 text-gray-500 italic">Klik na styk = zmień typ</div>
      </div>
    </div>
  );
};

export default ModuleLayoutEditor;
