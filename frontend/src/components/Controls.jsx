import React, { useState, useRef } from 'react';
import ModuleLayoutEditor from './ModuleLayoutEditor';
import {
  GeometrySection,
  RoofSection,
  DocksSection,
  CladdingSection,
  StructureSection,
  FireSafetySection,
  RoofLightsSection,
  TechnicalRoomsSection,
  ExternalOfficesSection,
  InternalOfficesSection,
  ReserveZonesSection,
  ClimateLoadsSection,
} from './sections';

// --- KOMPONENT ZWIJANEJ SEKCJI ---
const CollapsibleSection = ({ title, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-gray-100 last:border-0">
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className="w-full flex justify-between items-center py-3 px-1 text-left focus:outline-none hover:bg-gray-50 transition-colors"
      >
        <h3 className="text-[11px] font-black text-blue-900 uppercase tracking-wider">{title}</h3>
        <span className={`text-blue-500 transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      {isOpen && <div className="pb-4 pt-1 px-1 animate-fadeIn">{children}</div>}
    </div>
  );
};

// --- PANEL POŁĄCZEŃ MODUŁÓW ---
const ConnectionsPanel = ({ blocks, connections, onChange }) => {
  if (!connections || connections.length === 0) {
    return <p className="text-[9px] text-gray-400 italic">Przesuwaj moduły na rzucie aby stworzyć styki. Kliknij na styk aby zmienić typ połączenia.</p>;
  }
  return (
    <div className="flex flex-col gap-1">
      {connections.map((conn, ci) => {
        const modA = (blocks || [])[conn.moduleA];
        const modB = (blocks || [])[conn.moduleB];
        if (!modA || !modB) return null;
        const perpendicular = (modA.frame_orientation || 0) !== (modB.frame_orientation || 0);
        const heightDiff = Math.abs((modA.clear_height || 10) - (modB.clear_height || 10));
        const hasHeightDiff = heightDiff > 0.5;
        return (
          <div key={ci} className="p-1.5 bg-gray-50 rounded border border-gray-100 text-[8px]">
            <div className="flex items-center gap-1 mb-1">
              <span className="font-bold text-gray-700 truncate flex-1">{modA.block_id} ↔ {modB.block_id}</span>
              {hasHeightDiff && <span className="text-[7px] text-orange-600" title={`Różnica wysokości: ${heightDiff.toFixed(1)}m`}>Δh={heightDiff.toFixed(1)}m</span>}
              {perpendicular && <span className="text-amber-600 text-[7px]" title="Prostopadłe ramy">⚠90°</span>}
            </div>
            <select value={conn.type || 'expansion_joint'}
              onChange={(e) => {
                const newConns = [...connections];
                newConns[ci] = {...newConns[ci], type: e.target.value};
                onChange(newConns);
              }} className="w-full p-0.5 border rounded text-[8px] mb-1">
              <option value="expansion_joint">Dylatacja (bez ściany wewn.)</option>
              {!perpendicular && <option value="none">Bez ściany (scal w jedną przestrzeń)</option>}
              <option value="internal_wall">Ściana wewn. (bez odporności ogn.)</option>
              <option value="fire_wall">Ściana PPOŻ</option>
            </select>
            {conn.type === 'fire_wall' && (
              <select value={conn.rei_class || 'REI60'}
                onChange={(e) => {
                  const newConns = [...connections];
                  newConns[ci] = {...newConns[ci], rei_class: e.target.value};
                  onChange(newConns);
                }} className="w-full p-0.5 border rounded text-[7px] border-red-200 bg-red-50">
                <option value="REI60">REI 60</option>
                <option value="REI120">REI 120</option>
                <option value="REI240">REI 240</option>
              </select>
            )}
            <p className="text-[7px] text-gray-400 mt-0.5 leading-tight">
              {conn.type === 'expansion_joint' && (hasHeightDiff
                ? '⚡ Dylatacja: brak ściany wewnątrz, ściana zamykająca nad niższym dachem (attyka)'
                : '⚡ Dylatacja: brak ściany wewnątrz budynku, podwójne słupy')}
              {conn.type === 'none' && '→ Scalone w jedną przestrzeń: usuwa ściany i zdublowany rząd słupów na styku (kształt L/T/U)'}
              {conn.type === 'internal_wall' && '→ Ściana działowa bez odporności ogniowej'}
              {conn.type === 'fire_wall' && `→ Ściana PPOŻ ${conn.rei_class || 'REI60'} wystająca ≥0.3m ponad dach`}
            </p>
          </div>
        );
      })}
    </div>
  );
};

// --- GŁÓWNY KOMPONENT ---
const Controls = ({ params, setParams, onGenerate, isLoading, onPanelChange, catalog, roofSheetCatalog, thermalInsulationCatalog, waterproofingCatalog, soilCatalog, validation }) => {
  const fileInputRef = useRef(null);

  // --- onChange handler for Simple mode (top-level params) ---
  const handleSimpleChange = (updates) => {
    setParams(prev => ({ ...prev, ...updates }));
  };

  // --- onChange handler factory for Complex mode (per-block) ---
  const makeBlockHandler = (idx) => (updates) => {
    setParams(prev => {
      const nb = [...(prev.blocks || [])];
      nb[idx] = { ...nb[idx], ...updates };
      return { ...prev, blocks: nb };
    });
  };

  // --- ZAPIS / WCZYTANIE PROJEKTU ---
  const handleSaveProject = () => {
    const data = JSON.stringify(params, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const timestamp = new Date().toISOString().slice(0, 16).replace(/[T:]/g, "-");
    a.download = `hala_${params.width}x${params.length}_${timestamp}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleLoadProject = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const loaded = JSON.parse(evt.target.result);
        setParams(loaded);
      } catch (err) {
        alert("Nie udało się wczytać pliku projektu. Sprawdź czy to poprawny plik JSON.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  return (
    <div className="w-80 bg-white p-4 shadow-xl h-full flex flex-col z-10 relative">
      <h2 className="text-lg font-black text-gray-800 mb-3 border-b pb-2 text-center uppercase">Vibe Hall Builder</h2>

      <div className="flex gap-2 mb-3">
        <button onClick={handleSaveProject}
          className="flex-1 py-1.5 text-[9px] font-bold rounded border border-green-300 bg-green-50 text-green-700 hover:bg-green-100 uppercase tracking-wide">
          💾 Zapisz projekt
        </button>
        <button onClick={() => fileInputRef.current?.click()}
          className="flex-1 py-1.5 text-[9px] font-bold rounded border border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100 uppercase tracking-wide">
          📂 Wczytaj projekt
        </button>
        <input ref={fileInputRef} type="file" accept=".json" onChange={handleLoadProject} className="hidden" />
      </div>

      <div className="flex bg-gray-100 rounded p-1 mb-3">
        {['simple', 'complex'].map(type => (
          <button key={type} onClick={() => setParams(prev => ({...prev, hall_type: type}))}
            className={`flex-1 py-1 text-xs font-bold rounded uppercase ${params.hall_type === type ? 'bg-white shadow text-blue-600' : 'text-gray-400'}`}>
            {type}
          </button>
        ))}
      </div>

      {/* Lokalizacja / obciążenia klimatyczne — wspólne dla całej hali, niezależnie od trybu */}
      <CollapsibleSection title="Lokalizacja — obciążenia klimatyczne">
        <ClimateLoadsSection data={params} onChange={handleSimpleChange} soilCatalog={soilCatalog} />
      </CollapsibleSection>

      {/* ===================== SIMPLE MODE ===================== */}
      {params.hall_type === 'simple' && (
        <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
          <CollapsibleSection title="1. Geometria Główna" defaultOpen={true}>
            <GeometrySection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>

          <CollapsibleSection title="2. Geometria Dachu">
            <RoofSection data={params} onChange={handleSimpleChange} roofSheetCatalog={roofSheetCatalog} thermalInsulationCatalog={thermalInsulationCatalog} waterproofingCatalog={waterproofingCatalog} />
          </CollapsibleSection>

          <CollapsibleSection title="3. Logistyka i Doki" defaultOpen={true}>
            <DocksSection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>

          <CollapsibleSection title="Doświetlenie i Oddymianie">
            <RoofLightsSection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>

          <CollapsibleSection title="ŚCIANY ZEWNĘTRZNE">
            <CladdingSection data={params} onChange={handleSimpleChange} catalog={catalog} />
          </CollapsibleSection>

          <CollapsibleSection title="KONSTRUKCJA">
            <StructureSection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>

          <CollapsibleSection title="6. Bezpieczeństwo Pożarowe">
            <FireSafetySection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>

          <CollapsibleSection title="7. Pomieszczenia Techniczne">
            <TechnicalRoomsSection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>

          <CollapsibleSection title="8. Biura Zewnętrzne">
            <ExternalOfficesSection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>

          <CollapsibleSection title="9. Antresole Wewnętrzne">
            <InternalOfficesSection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>

          <CollapsibleSection title="10. Rezerwa pod Biura (Dach)">
            <ReserveZonesSection data={params} onChange={handleSimpleChange} />
          </CollapsibleSection>
        </div>
      )}

      {/* ===================== COMPLEX MODE ===================== */}
      {params.hall_type === 'complex' && (
        <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
          <CollapsibleSection title="Moduły Hali" defaultOpen={true}>
            <div className="flex flex-col gap-2">
              <button onClick={() => {
                const idx = (params.blocks || []).length + 1;
                const newBlock = {
                  block_id: `Moduł_${idx}`,
                  width: 30, length: 60, clear_height: 10, bay_spacing: 6,
                  roof_angle: 3, roof_drainage_type: 'gravity', number_of_aisles: 1,
                  frame_orientation: 0, position_x: (idx - 1) * 35, position_z: 0,
                  docks_config: {}, dock_zone_enabled: false, dock_zone_side: 'left',
                  dock_zone_width: 12, dock_zone_aisles: 1,
                  has_cladding: true, cladding_orientation: 'horizontal', cladding_panel_id: 'SP2B_E_PIR_100',
                  truss_depth: 0.6, purlin_spacing: 2.0, roof_sheet_id: 'T85_08',
                  column_method: 'default', foundation_method: 'default', foundation_depth: 1.0,
                  dock_foundation_depth: 1.2, plinth_top_level: 0.30,
                  fire_load_qd: 500, has_sprinklers: false, fire_walls: [],
                  roof_lights: [], technical_rooms: [], external_offices: [],
                  internal_offices: [], office_reserve_zones: [],
                  manual_column_sections: { external_main: [0.4,0.4], external_corner: [0.4,0.4], external_intermediate_cladding: [0.3,0.3], internal_main: [0.4,0.4] },
                  manual_sizes: { external_main: [2.5,4.0,0.45], external_corner: [2.5,4.0,0.45], external_intermediate_cladding: [1.5,1.5,0.40], internal_main: [2.5,2.5,0.45] },
                };
                setParams(prev => ({...prev, blocks: [...(prev.blocks || []), newBlock]}));
              }} className="w-full py-2 bg-green-50 text-green-700 text-[10px] font-bold rounded border border-green-200 hover:bg-green-100">
                + Dodaj Moduł
              </button>

              {(params.blocks || []).map((block, idx) => {
                const isSelected = block.block_id === params._selectedModuleId;
                const blockHandler = makeBlockHandler(idx);
                return (
                  <div key={block.block_id || idx} className={`p-2 rounded border ${isSelected ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-gray-50'}`}
                    onClick={() => setParams(prev => ({...prev, _selectedModuleId: block.block_id}))}>

                    {/* Header */}
                    <div className="flex justify-between items-center mb-1">
                      <input type="text" value={block.block_id}
                        onChange={(e) => blockHandler({ block_id: e.target.value })}
                        onClick={(e) => e.stopPropagation()}
                        className="text-[10px] font-black text-blue-800 uppercase bg-transparent border-b border-transparent hover:border-gray-300 focus:border-blue-400 outline-none w-28" />
                      <button onClick={(e) => {
                        e.stopPropagation();
                        const nb = [...params.blocks]; nb.splice(idx, 1);
                        setParams(prev => ({...prev, blocks: nb}));
                      }} className="text-[8px] bg-red-50 text-red-600 px-2 py-0.5 rounded hover:bg-red-100">✕</button>
                    </div>

                    {/* Orientation + drainage (always visible) */}
                    <div className="flex gap-2 mb-1" onClick={(e) => e.stopPropagation()}>
                      <div className="flex-1">
                        <span className="text-[7px] font-bold text-gray-500 uppercase">Orientacja ram</span>
                        <select value={block.frame_orientation || 0}
                          onChange={(e) => blockHandler({ frame_orientation: parseInt(e.target.value) })}
                          className="w-full p-0.5 border rounded text-[8px]">
                          <option value="0">↕ Wzdłuż szerokości</option>
                          <option value="90">↔ Wzdłuż długości (90°)</option>
                        </select>
                      </div>
                      <div className="flex-1">
                        <span className="text-[7px] font-bold text-gray-500 uppercase">Odwodnienie</span>
                        <select value={block.roof_drainage_type || 'gravity'}
                          onChange={(e) => blockHandler({ roof_drainage_type: e.target.value })}
                          className="w-full p-0.5 border rounded text-[8px]">
                          <option value="gravity">Grawitacyjne</option>
                          <option value="vacuum">Podciśnieniowe</option>
                        </select>
                      </div>
                    </div>

                    {/* Full parameter sections (expandable) */}
                    <details className="mt-1 border-t border-gray-200 pt-1" onClick={(e) => e.stopPropagation()}>
                      <summary className="text-[8px] font-bold text-indigo-600 cursor-pointer hover:text-indigo-800 select-none">
                        ▸ Pełne parametry modułu
                      </summary>
                      <div className="mt-2 flex flex-col gap-3">

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Geometria</span>
                          <GeometrySection data={block} onChange={blockHandler} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Dach</span>
                          <RoofSection data={block} onChange={blockHandler} roofSheetCatalog={roofSheetCatalog} thermalInsulationCatalog={thermalInsulationCatalog} waterproofingCatalog={waterproofingCatalog} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Logistyka i Doki</span>
                          <DocksSection data={block} onChange={blockHandler} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Doświetlenie</span>
                          <RoofLightsSection data={block} onChange={blockHandler} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Ściany zewnętrzne</span>
                          <CladdingSection data={block} onChange={blockHandler} catalog={catalog} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Konstrukcja</span>
                          <StructureSection data={block} onChange={blockHandler} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">PPOŻ</span>
                          <FireSafetySection data={block} onChange={blockHandler} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Pomieszczenia techniczne</span>
                          <TechnicalRoomsSection data={block} onChange={blockHandler} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Biura zewnętrzne</span>
                          <ExternalOfficesSection data={block} onChange={blockHandler} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Antresole</span>
                          <InternalOfficesSection data={block} onChange={blockHandler} />
                        </div>

                        <div className="border border-gray-100 rounded p-1.5">
                          <span className="text-[8px] font-bold text-gray-600 block mb-1 uppercase">Rezerwa pod biura</span>
                          <ReserveZonesSection data={block} onChange={blockHandler} />
                        </div>

                      </div>
                    </details>
                  </div>
                );
              })}
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Rzut — Rozmieszczenie Modułów" defaultOpen={true}>
            <div className="h-[350px]">
              <ModuleLayoutEditor
                modules={params.blocks || []}
                setModules={(newBlocks) => setParams(prev => ({...prev, blocks: newBlocks}))}
                connections={params.module_connections || []}
                setConnections={(newConns) => setParams(prev => ({...prev, module_connections: newConns}))}
                selectedModuleId={params._selectedModuleId || null}
                setSelectedModuleId={(id) => setParams(prev => ({...prev, _selectedModuleId: id}))}
              />
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Połączenia Modułów">
            <ConnectionsPanel
              blocks={params.blocks || []}
              connections={params.module_connections || []}
              onChange={(newConns) => setParams(prev => ({...prev, module_connections: newConns}))}
            />
          </CollapsibleSection>
        </div>
      )}

      <button onClick={onGenerate} disabled={isLoading} 
        className="mt-3 w-full py-3 rounded-lg text-white font-black uppercase tracking-widest text-[11px] bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300">
        {isLoading ? 'Przeliczanie...' : 'Buduj Model 3D'}
      </button>

      {validation && validation.clashes && validation.clashes.length > 0 && (
        <div className="mt-2 max-h-32 overflow-y-auto">
          {validation.clashes.map((clash, idx) => (
            <div key={idx} className={`text-[9px] p-1.5 mb-1 rounded border ${clash.severity === 'error' ? 'bg-red-50 border-red-200 text-red-700' : 'bg-yellow-50 border-yellow-200 text-yellow-700'}`}>
              <span className="font-bold uppercase">{clash.severity === 'error' ? 'BŁĄD' : 'UWAGA'}:</span> {clash.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Controls;
