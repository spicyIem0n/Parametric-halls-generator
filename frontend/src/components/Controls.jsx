import React, { useState, useRef } from 'react';
import ModuleLayoutEditor from './ModuleLayoutEditor';

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

// --- KOMPONENT MAPY DOKÓW ---
const DockGridSelector = ({ params, setParams }) => {
  const numBays = Math.max(1, Math.round(params.length / params.bay_spacing));
  const slotsPerBay = Math.max(1, Math.floor(params.bay_spacing / 4.0));
  const [openingType, setOpeningType] = React.useState("dock");
  const [lastClicked, setLastClicked] = React.useState(null);

  const flatToKey = (side, flat) => `${side}-${Math.floor(flat / slotsPerBay)}-${flat % slotsPerBay}`;

  const applyToSlot = (side, flatIndex) => {
    const key = flatToKey(side, flatIndex);
    setParams(prev => {
      const newConfig = { ...prev.docks_config };
      if (openingType === "none") delete newConfig[key];
      else newConfig[key] = openingType;
      return { ...prev, docks_config: newConfig };
    });
  };

  const applyRange = (side, from, to) => {
    const min = Math.min(from, to), max = Math.max(from, to);
    setParams(prev => {
      const newConfig = { ...prev.docks_config };
      for (let f = min; f <= max; f++) {
        const key = flatToKey(side, f);
        if (openingType === "none") delete newConfig[key];
        else newConfig[key] = openingType;
      }
      return { ...prev, docks_config: newConfig };
    });
  };

  const handleClick = (side, flatIndex, e) => {
    if (e.shiftKey && lastClicked && lastClicked.side === side) {
      applyRange(side, lastClicked.flatIndex, flatIndex);
    } else {
      applyToSlot(side, flatIndex);
    }
    setLastClicked({ side, flatIndex });
  };

  const fillSide = (side) => {
    const newConfig = { ...params.docks_config };
    const fillType = openingType === "none" ? "dock" : openingType;
    for (let i = 0; i < numBays; i++)
      for (let k = 0; k < slotsPerBay; k++) newConfig[`${side}-${i}-${k}`] = fillType;
    setParams(prev => ({ ...prev, docks_config: newConfig }));
  };
  const clearSide = (side) => {
    const newConfig = { ...params.docks_config };
    for (let i = 0; i < numBays; i++)
      for (let k = 0; k < slotsPerBay; k++) delete newConfig[`${side}-${i}-${k}`];
    setParams(prev => ({ ...prev, docks_config: newConfig }));
  };

  return (
    <div className="bg-white rounded border border-gray-200 p-2 shadow-sm">
      <div className="mb-2">
        <span className="text-[9px] font-bold text-gray-500 uppercase block mb-1">Rodzaj otworu (klik / Shift+klik = zakres)</span>
        <select value={openingType} onChange={(e) => setOpeningType(e.target.value)} className="w-full p-1.5 border rounded text-[10px] font-bold bg-gray-50">
          <option value="dock">Dok przeładunkowy</option>
          <option value="gate">Brama kurierska</option>
          <option value="none">Ściana pełna (usuń)</option>
        </select>
      </div>
      <div className="flex justify-between mb-2">
        <div className="flex gap-1 flex-col">
          <button onClick={() => fillSide("left")} className="text-[8px] bg-blue-50 text-blue-600 px-1 py-1 rounded">Wypełnij L</button>
          <button onClick={() => clearSide("left")} className="text-[8px] bg-red-50 text-red-600 px-1 py-1 rounded">Czyść L</button>
        </div>
        <div className="flex gap-1 flex-col">
          <button onClick={() => fillSide("right")} className="text-[8px] bg-blue-50 text-blue-600 px-1 py-1 rounded">Wypełnij R</button>
          <button onClick={() => clearSide("right")} className="text-[8px] bg-red-50 text-red-600 px-1 py-1 rounded">Czyść R</button>
        </div>
      </div>
      <div className="flex justify-between gap-2">
        {["left", "right"].map((side) => (
          <div key={side} className="flex-1 flex flex-col gap-1">
            <span className="text-[9px] font-bold text-center text-gray-400 uppercase">{side === "left" ? "LEWA" : "PRAWA"}</span>
            {[...Array(numBays)].map((_, i) => (
              <div key={`${side}-bay-${i}`} className="flex gap-1 border border-dashed border-gray-300 p-1 rounded bg-gray-50">
                {[...Array(slotsPerBay)].map((_, k) => {
                  const flat = i * slotsPerBay + k;
                  const val = params.docks_config[`${side}-${i}-${k}`];
                  return (
                    <button key={flat} onClick={(e) => handleClick(side, flat, e)}
                      className={`flex-1 h-6 rounded text-[7px] border font-bold flex items-center justify-center select-none
                        ${val === "dock" ? "bg-blue-500 text-white" : val === "gate" ? "bg-orange-500 text-white" : "bg-white text-gray-400"}`}>
                      {val === "dock" ? "DOK" : val === "gate" ? "BRM" : "-"}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};


const Controls = ({ params, setParams, onGenerate, isLoading, onPanelChange, catalog, roofSheetCatalog, validation }) => {
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const STRING_FIELDS = new Set(["roof_drainage_type", "column_method", "foundation_method", "floor_base_type", "cladding_orientation", "cladding_panel_id", "hall_type"]);
    const INTEGER_FIELDS = new Set(["number_of_aisles", "drainage_zones_x", "drainage_zones_z"]);
    setParams(prev => {
      if (type === "checkbox") return { ...prev, [name]: checked };
      if (STRING_FIELDS.has(name) || type === "select-one") return { ...prev, [name]: value };
      const parsed = parseFloat(value);
      if (!Number.isFinite(parsed)) return prev;
      return { ...prev, [name]: INTEGER_FIELDS.has(name) ? Math.round(parsed) : parsed };
    });
  };

  // --- ZAPIS / WCZYTANIE PROJEKTU ---
  const fileInputRef = useRef(null);

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

      {params.hall_type === 'simple' && (
        <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
          
          <CollapsibleSection title="1. Geometria Główna" defaultOpen={true}>
            <div className="flex flex-col gap-3">
              {[
                { name: 'width', label: 'Szerokość [m]', min: 10, max: 180, step: "1" },
                { name: 'length', label: 'Długość [m]', min: 10, max: 360, step: "1" },
                { name: 'clear_height', label: 'Wys. w świetle [m]', min: 4, max: 18, step: "0.5" },
                { name: 'number_of_aisles', label: 'Ilość naw [szt]', min: 1, max: 12, step: "1" },
                { name: 'bay_spacing', label: 'Rozstaw ram [m]', min: 4, max: 12, step: "0.5" }
              ].map(f => (
                <div key={f.name} className="flex flex-col">
                  <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                    <label>{f.label}</label><input type="number" name={f.name} min={f.min} max={f.max} step={f.step} value={params[f.name]} onChange={handleChange} className="w-14 text-right text-blue-600 font-bold bg-transparent border-b border-blue-200 focus:outline-none text-[10px]" />
                  </div>
                  <input type="range" {...f} value={params[f.name]} onChange={handleChange} className="w-full h-1 bg-gray-200 rounded accent-blue-600" />
                </div>
              ))}
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="2. Geometria Dachu">
            <div className="flex flex-col gap-3">
              <select name="roof_drainage_type" value={params.roof_drainage_type} onChange={handleChange} className="w-full p-2 border rounded bg-gray-50 text-[10px] font-bold">
                <option value="gravity">Grawitacyjne (Dwuspadowy)</option>
                <option value="vacuum">Podciśnieniowe (Koperty)</option>
              </select>
              
              {params.roof_drainage_type === 'gravity' && (
                <div className="flex flex-col">
                  <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase"><label>Kąt dachu [°]</label> <span className="text-blue-600">{params.roof_angle}</span></div>
                  <input type="range" name="roof_angle" min="2" max="35" step="1" value={params.roof_angle} onChange={handleChange} className="w-full h-1 bg-gray-200 rounded" />
                </div>
              )}
              
              <div className="flex flex-col border-t pt-2 mt-2">
                <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase"><label>Max. rozstaw płatwi [m]</label> <span className="text-blue-600">{params.purlin_spacing}</span></div>
                <input type="range" name="purlin_spacing" min="1" max="4" step="0.5" value={params.purlin_spacing} onChange={handleChange} className="w-full h-1 bg-gray-200 rounded" />
              <div className="flex flex-col border-t pt-2 mt-2">
                <span className="text-[10px] font-bold text-gray-500 uppercase mb-1">Blacha trapezowa dachowa</span>
                {roofSheetCatalog && (
                  <select name="roof_sheet_id" value={params.roof_sheet_id || "T85_08"} onChange={(e) => {
                    const sheet = roofSheetCatalog[e.target.value];
                    setParams(prev => ({ ...prev, roof_sheet_id: e.target.value, roof_sheet_height: sheet.height / 1000 }));
                  }} className="w-full p-2 border rounded text-[10px] font-bold bg-gray-50">
                    {Object.entries(roofSheetCatalog || {}).map(([id, sheet]) => (
                      <option key={id} value={id}>{sheet.name} (h={sheet.height}mm, gr={sheet.thickness}mm, rozp. do {sheet.span}m)</option>
                    ))}
                  </select>
                )}
              </div>
              <div className="flex flex-col border-t pt-2 mt-2">
                <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                  <label>Wys. konstrukcji dachu [m]</label>
                  <input type="number" name="truss_depth" min="0.3" max="2.5" step="0.1" value={params.truss_depth} onChange={handleChange} className="w-14 text-right text-blue-600 font-bold bg-transparent border-b border-blue-200 focus:outline-none text-[10px]" />
                </div>
                <input type="range" name="truss_depth" min="0.3" max="2.5" step="0.1" value={params.truss_depth} onChange={handleChange} className="w-full h-1 bg-gray-200 rounded accent-blue-600" />
                <div className="mt-1 text-[9px] text-gray-400">
                  Najwy\u017cszy pkt dachu (g\u00f3rna fa\u0142da blachy): <span className="text-blue-600 font-bold">{(parseFloat(params.clear_height || 0) + parseFloat(params.truss_depth || 0) + parseFloat(params.roof_sheet_height || 0.085)).toFixed(2)} m</span>
                </div>
              </div>
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="3. Logistyka i Doki" defaultOpen={true}>
            <DockGridSelector params={params} setParams={setParams} />
          </CollapsibleSection>

          {params.number_of_aisles > 1 && (
          <CollapsibleSection title="Strefa Dokowa">
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase text-gray-500">Strefa dokowa aktywna</span>
                <input type="checkbox" name="dock_zone_enabled" checked={params.dock_zone_enabled || false} onChange={handleChange} className="rounded" />
              </div>

              {params.dock_zone_enabled && (
                <div className="flex flex-col gap-2 bg-blue-50/50 p-2 rounded border border-blue-100">
                  <div className="flex flex-col">
                    <span className="text-[10px] font-bold text-gray-500 uppercase mb-1">Strona strefy dokowej</span>
                    <select name="dock_zone_side" value={params.dock_zone_side || "left"} onChange={handleChange} className="w-full p-2 border rounded text-[10px] font-bold bg-white">
                      <option value="left">Lewa (strefa po lewej)</option>
                      <option value="right">Prawa (strefa po prawej)</option>
                      <option value="both">Obie strony</option>
                    </select>
                  </div>

                  <div className="flex flex-col">
                    <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                      <label>Szer. nawy dokowej [m]</label>
                      <input type="number" name="dock_zone_width" min="6" max="24" step="0.5" value={params.dock_zone_width || 12} onChange={handleChange} className="w-14 text-right text-blue-600 font-bold bg-transparent border-b border-blue-200 focus:outline-none text-[10px]" />
                    </div>
                    <input type="range" name="dock_zone_width" min="6" max="24" step="0.5" value={params.dock_zone_width || 12} onChange={handleChange} className="w-full h-1 bg-blue-200 rounded accent-blue-600" />
                  </div>

                  <div className="flex flex-col">
                    <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                      <label>Ile naw skrajnych w strefie</label>
                      <span className="text-blue-600">{params.dock_zone_aisles || 1}</span>
                    </div>
                    <input type="range" name="dock_zone_aisles" min="1" max={Math.max(1, (params.number_of_aisles || 2) - 1)} step="1" value={params.dock_zone_aisles || 1} onChange={handleChange} className="w-full h-1 bg-blue-200 rounded accent-blue-600" />
                  </div>

                  <div className="text-[9px] text-gray-400 mt-1">
                    Nawa dokowa: <span className="text-blue-600 font-bold">{params.dock_zone_width || 12}m</span> |
                    Pozosta\u0142e nawy: <span className="text-blue-600 font-bold">{((params.width - (params.dock_zone_width || 12) * (params.dock_zone_aisles || 1) * (params.dock_zone_side === "both" ? 2 : 1)) / Math.max(1, params.number_of_aisles - (params.dock_zone_aisles || 1) * (params.dock_zone_side === "both" ? 2 : 1))).toFixed(1)}m</span>
                  </div>
                </div>
              )}
            </div>
          </CollapsibleSection>
          )}


          <CollapsibleSection title="Doświetlenie i Oddymianie">
            <div className="flex flex-col gap-3">
              {["main", ...(params.dock_zone_enabled ? ["dock_zone"] : [])].map(zoneId => {
                const zoneConfig = (params.roof_lights || []).find(z => z.zone_id === zoneId) || { zone_id: zoneId, items: [] };
                const zoneItems = zoneConfig.items || [];
                const zoneName = zoneId === "main" ? "Strefa magazynowa" : "Strefa dokowa";

                // Obliczenia powierzchni
                const zoneWidth = zoneId === "dock_zone" ? (params.dock_zone_width || 12) * (params.dock_zone_side === "both" ? 2 : 1) : params.width - ((params.dock_zone_enabled && params.dock_zone_side !== "both") ? (params.dock_zone_width || 12) : (params.dock_zone_enabled ? (params.dock_zone_width || 12) * 2 : 0));
                const zoneArea = zoneWidth * params.length;
                let skylightArea = 0, ventArea = 0;
                zoneItems.forEach(item => {
                  const a = item.width * item.length * item.quantity;
                  if (item.item_type === "skylight" || item.item_type === "light_strip") skylightArea += a;
                  if (item.item_type === "smoke_vent") ventArea += a;
                  if (item.item_type === "light_strip_with_vents") {
                    const ventsInStrip = item.width * (item.vent_length || 2) * (item.vent_count || 0) * item.quantity;
                    skylightArea += a - ventsInStrip;
                    ventArea += ventsInStrip;
                  }
                });

                return (
                  <div key={zoneId} className="border border-gray-200 rounded p-2 mb-2">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-[10px] font-black text-cyan-800 uppercase">{zoneName}</span>
                      <button onClick={() => {
                        const newItem = { item_id: `${zoneId}_${Date.now()}`, item_type: "skylight", width: 2.0, length: 3.0, quantity: 4, vent_count: 2, vent_length: 2.0 };
                        const newZones = [...(params.roof_lights || [])];
                        const idx = newZones.findIndex(z => z.zone_id === zoneId);
                        if (idx >= 0) { newZones[idx] = { ...newZones[idx], items: [...newZones[idx].items, newItem] }; }
                        else { newZones.push({ zone_id: zoneId, items: [newItem] }); }
                        setParams(prev => ({ ...prev, roof_lights: newZones }));
                      }} className="text-[8px] bg-cyan-50 text-cyan-700 px-2 py-1 rounded">+ Pozycja</button>
                    </div>

                    {zoneItems.map((item, itemIdx) => (
                      <div key={item.item_id} className="bg-gray-50 p-1.5 rounded border border-gray-100 mb-1">
                        <div className="flex gap-1 items-center mb-1">
                          <select value={item.item_type} onChange={(e) => {
                            const newType = e.target.value;
                            const isStrip = newType === "light_strip" || newType === "light_strip_with_vents";
                            const fullStripLen = Math.max(6, Math.round((params.length - 2) * 2) / 2);
                            const newZones = [...(params.roof_lights || [])];
                            const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                            if (zIdx >= 0) {
                              const newItems = [...newZones[zIdx].items];
                              const cur = newItems[itemIdx];
                              let len = cur.length;
                              if (isStrip && len < params.length * 0.5) len = fullStripLen;
                              if (!isStrip && len > 10) len = 3.0;
                              newItems[itemIdx] = { ...cur, item_type: newType, length: len };
                              newZones[zIdx] = { ...newZones[zIdx], items: newItems };
                            }
                            setParams(prev => ({ ...prev, roof_lights: newZones }));
                          }} className="flex-1 p-1 border text-[8px] rounded">
                            <option value="skylight">Świetlik</option>
                            <option value="smoke_vent">Klapa dymowa</option>
                            <option value="light_strip">Pasmo świetlne</option>
                            <option value="light_strip_with_vents">Pasmo z klapami</option>
                          </select>
                          <button onClick={() => {
                            const newZones = [...(params.roof_lights || [])];
                            const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                            if (zIdx >= 0) { const newItems = [...newZones[zIdx].items]; newItems.splice(itemIdx, 1); newZones[zIdx] = {...newZones[zIdx], items: newItems}; }
                            setParams(prev => ({ ...prev, roof_lights: newZones }));
                          }} className="text-[8px] text-red-500 px-1">X</button>
                        </div>
                        <div className="grid grid-cols-3 gap-1">
                          <div className="flex flex-col"><span className="text-[7px] text-gray-400">Szer[m]</span>
                            <input type="number" step="0.5" min="0.5" max="6" value={item.width} onChange={(e) => {
                              const newZones = [...(params.roof_lights || [])]; const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                              if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], width: parseFloat(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                              setParams(prev => ({...prev, roof_lights: newZones}));
                            }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                          <div className="flex flex-col"><span className="text-[7px] text-gray-400">Dł[m]</span>
                            <input type="number" step="0.5" min="1" max="400" value={item.length} onChange={(e) => {
                              const newZones = [...(params.roof_lights || [])]; const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                              if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], length: parseFloat(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                              setParams(prev => ({...prev, roof_lights: newZones}));
                            }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                          <div className="flex flex-col"><span className="text-[7px] text-gray-400">Ilość</span>
                            <input type="number" step="1" min="1" max="50" value={item.quantity} onChange={(e) => {
                              const newZones = [...(params.roof_lights || [])]; const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                              if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], quantity: parseInt(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                              setParams(prev => ({...prev, roof_lights: newZones}));
                            }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                        </div>
                        {item.item_type === "light_strip_with_vents" && (
                          <div className="grid grid-cols-2 gap-1 mt-1 border-t pt-1">
                            <div className="flex flex-col"><span className="text-[7px] text-gray-400">Klap [szt]</span>
                              <input type="number" step="1" min="1" max="20" value={item.vent_count} onChange={(e) => {
                                const newZones = [...(params.roof_lights || [])]; const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                                if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], vent_count: parseInt(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                                setParams(prev => ({...prev, roof_lights: newZones}));
                              }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                            <div className="flex flex-col"><span className="text-[7px] text-gray-400">Dł klapy[m]</span>
                              <input type="number" step="0.5" min="1" max="6" value={item.vent_length} onChange={(e) => {
                                const newZones = [...(params.roof_lights || [])]; const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                                if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], vent_length: parseFloat(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                                setParams(prev => ({...prev, roof_lights: newZones}));
                              }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                          </div>
                        )}
                      </div>
                    ))}

                    <div className="bg-cyan-50/50 rounded p-1.5 mt-1 text-[8px] text-gray-600">
                      <div>Pow. świetlików: <b>{skylightArea.toFixed(1)} m²</b></div>
                      <div>Pow. klap dymowych: <b>{ventArea.toFixed(1)} m²</b></div>
                      <div>Łącznie: <b>{(skylightArea + ventArea).toFixed(1)} m²</b></div>
                      <div>Udział w strefie ({zoneArea.toFixed(0)} m²): <b className="text-cyan-700">{zoneArea > 0 ? ((skylightArea + ventArea) / zoneArea * 100).toFixed(2) : 0}%</b></div>
                    </div>
                  </div>
                );
              })}

              <div className="bg-gray-100 rounded p-1.5 text-[8px] text-gray-700 font-bold">
                Uśredniony wsp. doświetlenia+oddymiania / pow. budynku: <span className="text-cyan-700">
                  {(() => {
                    let totalLight = 0, totalVent = 0;
                    (params.roof_lights || []).forEach(z => (z.items || []).forEach(item => {
                      const a = item.width * item.length * item.quantity;
                      if (item.item_type === "skylight" || item.item_type === "light_strip") totalLight += a;
                      if (item.item_type === "smoke_vent") totalVent += a;
                      if (item.item_type === "light_strip_with_vents") {
                        const vInS = item.width * (item.vent_length||2) * (item.vent_count||0) * item.quantity;
                        totalLight += a - vInS;
                        totalVent += vInS;
                      }
                    }));
                    const buildingArea = params.width * params.length;
                    return buildingArea > 0 ? ((totalLight + totalVent) / buildingArea * 100).toFixed(2) + "%" : "0%";
                  })()}
                </span>
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="ŚCIANY ZEWNĘTRZNE">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold uppercase text-gray-500">Płyty ścienne</span>
              <input type="checkbox" name="has_cladding" checked={params.has_cladding} onChange={handleChange} className="rounded" />
            </div>
            {params.has_cladding && (
              <select value={params.cladding_panel_id} onChange={(e) => onPanelChange(e.target.value)} className="w-full p-2 border rounded text-[10px] font-bold text-blue-900 bg-blue-50">
                {Object.entries(catalog).map(([id, panel]) => (
                  <option key={id} value={id}>{panel.name} ({panel.thickness}mm)</option>
                ))}
              </select>
            )}
            {params.has_cladding && (
              <div className="mt-2">
                <span className="text-[10px] font-bold uppercase text-gray-500 block mb-1">Układ płyt</span>
                <select name="cladding_orientation" value={params.cladding_orientation} onChange={handleChange} className="w-full p-2 border rounded text-[10px] font-bold bg-gray-50">
                  <option value="horizontal">Poziomy (standardowy)</option>
                  <option value="vertical">Pionowy (z ryglami montażowymi)</option>
                </select>
              </div>
            )}
          </CollapsibleSection>
<CollapsibleSection title="KONSTRUKCJA">
            <div className="flex flex-col gap-4">
              
              {/* --- SŁUPY --- */}
              <div>
                <span className="text-[10px] font-bold text-gray-500 uppercase mb-1 block">Metoda doboru słupów</span>
                <select name="column_method" value={params.column_method} onChange={handleChange} className="w-full p-2 border rounded text-[10px] font-bold bg-gray-50">
                  <option value="default">Domyślne przekroje</option>
                  <option value="manual">Ręczne przekroje [X, Z]</option>
                </select>
                
                {params.column_method === 'manual' && (
                  <div className="mt-2 bg-gray-50 p-2 rounded flex flex-col gap-2 border border-gray-200">
                    {[
                      { key: 'external_main', label: 'Słupy główne zewnętrzne' },
                      { key: 'external_corner', label: 'Słupy zewnętrzne narożne' },
                      { key: 'external_intermediate_cladding', label: 'Słupy pośrednie pod obudowę' },
                      { key: 'internal_main', label: 'Słupy wewnętrzne' },
                    ].map(cat => (
                      <div key={cat.key} className="flex flex-col gap-1">
                        <label className="text-[8px] font-bold text-gray-500 uppercase">{cat.label}</label>
                        <div className="flex gap-1">
                          {(params.manual_column_sections[cat.key] || [0.4, 0.4]).map((v, i) => (
                            <input key={i} type="number" step="0.05" value={v} onChange={(e) => {
                              setParams(prev => {
                                const newSections = { ...prev.manual_column_sections };
                                newSections[cat.key] = [...(newSections[cat.key] || [0.4, 0.4])];
                                newSections[cat.key][i] = parseFloat(e.target.value) || 0;
                                return { ...prev, manual_column_sections: newSections };
                              });
                            }} className="w-full p-1 border text-[10px] text-center rounded font-mono" />
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* --- FUNDAMENTY --- */}
              <div className="border-t border-gray-100 pt-3">
                <span className="text-[10px] font-bold text-gray-500 uppercase mb-1 block">Metoda doboru fundamentów</span>
                <select name="foundation_method" value={params.foundation_method} onChange={handleChange} className="w-full p-2 border rounded text-[10px] font-bold bg-gray-50">
                  <option value="default">Gabaryty domyślne</option>
                  <option value="manual">Gabaryty ręczne [A, B, H]</option>
                </select>
                
                {params.foundation_method === 'manual' && (
                  <div className="mt-2 bg-blue-50/50 p-2 rounded flex flex-col gap-2 border border-blue-100">
                    {[
                      { key: 'external_main', label: 'Stopy pod słupy główne zewn.' },
                      { key: 'external_corner', label: 'Stopy pod słupy narożne' },
                      { key: 'external_intermediate_cladding', label: 'Stopy pod słupy pośrednie' },
                      { key: 'internal_main', label: 'Stopy pod słupy wewnętrzne' },
                    ].map(cat => (
                      <div key={cat.key} className="flex flex-col gap-1">
                        <label className="text-[8px] font-bold text-gray-500 uppercase">{cat.label}</label>
                        <div className="flex gap-1">
                          {(params.manual_sizes[cat.key] || [2.0, 2.0, 0.5]).map((v, i) => (
                            <input key={i} type="number" step="0.1" value={v} onChange={(e) => {
                              setParams(prev => {
                                const newSizes = { ...prev.manual_sizes };
                                newSizes[cat.key] = [...(newSizes[cat.key] || [2.0, 2.0, 0.5])];
                                newSizes[cat.key][i] = parseFloat(e.target.value) || 0;
                                return { ...prev, manual_sizes: newSizes };
                              });
                            }} className="w-full p-1 border text-[10px] text-center rounded font-mono" />
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="flex flex-col gap-2 mt-4">
                  <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                    <label>Zagłębienie główne [m]</label> <span className="text-blue-600">{params.foundation_depth}</span>
                  </div>
                  <input type="range" name="foundation_depth" min="0.5" max="2.0" step="0.1" value={params.foundation_depth} onChange={handleChange} className="w-full h-1 bg-gray-200 rounded accent-blue-600" />
                  
                  <div className="flex justify-between text-[10px] font-bold text-orange-600 uppercase mt-2">
                    <label>Zagłębienie dokowe [m]</label> <span className="text-orange-600">{params.dock_foundation_depth}</span>
                  </div>
                  <input type="range" name="dock_foundation_depth" min="0.8" max="2.5" step="0.1" value={params.dock_foundation_depth} onChange={handleChange} className="w-full h-1 bg-orange-200 rounded accent-orange-600" />
                </div>
              </div>
              
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="6. Bezpieczeństwo Pożarowe">
            <div className="flex flex-col gap-3">
              <div className="flex flex-col">
                <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                  <label>Obciążenie ogniowe Qd [MJ/m²]</label>
                  <span className="text-red-600">{params.fire_load_qd}</span>
                </div>
                <input type="range" name="fire_load_qd" min="100" max="5000" step="100" value={params.fire_load_qd} onChange={handleChange} className="w-full h-1 bg-red-200 rounded accent-red-600" />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase text-gray-500">Instalacja tryskaczowa</span>
                <input type="checkbox" name="has_sprinklers" checked={params.has_sprinklers} onChange={handleChange} className="rounded" />
              </div>

              <div className="bg-red-50 border border-red-200 rounded p-2 mt-1">
                <span className="text-[9px] font-bold text-red-800 uppercase block mb-1">Klasyfikacja automatyczna</span>
                <span className="text-[10px] text-red-700">
                  {params.fire_load_qd <= 500 ? 'Klasa E — brak wymogów' :
                   params.fire_load_qd <= 1000 ? 'Klasa D — R30 (konstrukcja główna)' :
                   params.fire_load_qd <= 2000 ? 'Klasa C — R60 / EI60' :
                   params.fire_load_qd <= 4000 ? 'Klasa B — R120 / EI120' :
                   'Klasa A — R240 / EI240'}
                </span>
              </div>

              <div className="border-t border-red-200 pt-2 mt-2">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[9px] font-bold text-red-800 uppercase">Ściany oddzielenia (ŚOP)</span>
                  <button onClick={() => {
                    const numBays = Math.max(1, Math.round(params.length / params.bay_spacing));
                    const midAxis = Math.min(Math.floor(numBays / 2), numBays);
                    const newFW = { axis_index: midAxis, rei_class: 'REI120', top_type: 'parapet_above_roof' };
                    setParams(prev => ({...prev, fire_walls: [...(prev.fire_walls || []), newFW]}));
                  }} className="text-[8px] bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200">+ ŚOP</button>
                </div>
                {(params.fire_walls || []).map((fw, idx) => (
                  <div key={idx} className="flex gap-1 items-center mb-1 bg-white p-1 rounded border border-red-100">
                    <span className="text-[8px] font-bold text-gray-500 w-8">Oś</span>
                    <input type="number" min="1" max={Math.max(1, Math.round(params.length / params.bay_spacing)) - 1} value={fw.axis_index}
                      onChange={(e) => {
                        const newFW = [...params.fire_walls];
                        newFW[idx] = {...newFW[idx], axis_index: parseInt(e.target.value) || 1};
                        setParams(prev => ({...prev, fire_walls: newFW}));
                      }} className="w-10 p-0.5 border text-[9px] text-center rounded" />
                    <select value={fw.rei_class} onChange={(e) => {
                      const newFW = [...params.fire_walls];
                      newFW[idx] = {...newFW[idx], rei_class: e.target.value};
                      setParams(prev => ({...prev, fire_walls: newFW}));
                    }} className="flex-1 p-0.5 border text-[8px] rounded">
                      <option value="REI60">REI60</option>
                      <option value="REI120">REI120</option>
                      <option value="REI240">REI240</option>
                    </select>
                    <select value={fw.top_type} onChange={(e) => {
                      const newFW = [...params.fire_walls];
                      newFW[idx] = {...newFW[idx], top_type: e.target.value};
                      setParams(prev => ({...prev, fire_walls: newFW}));
                    }} className="flex-1 p-0.5 border text-[8px] rounded">
                      <option value="parapet_above_roof">Attyka</option>
                      <option value="non_combustible_strip">Pas dachu</option>
                    </select>
                    <button onClick={() => {
                      const newFW = [...params.fire_walls];
                      newFW.splice(idx, 1);
                      setParams(prev => ({...prev, fire_walls: newFW}));
                    }} className="text-[8px] text-red-500 px-1">X</button>
                  </div>
                ))}
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="7. Pomieszczenia Techniczne">
            <div className="flex flex-col gap-2">
              <button onClick={() => {
                const newRoom = {
                  room_id: `tech_${(params.technical_rooms || []).length + 1}`,
                  width: 6, length: 4, height: 3,
                  position_anchor: 'corner_left_front', position_offset: [0, 0, 0],
                  fire_rating: 'REI120', has_own_roof: true, floor_level: 0
                };
                setParams(prev => ({...prev, technical_rooms: [...(prev.technical_rooms || []), newRoom]}));
              }} className="w-full py-1.5 bg-purple-50 text-purple-700 text-[10px] font-bold rounded border border-purple-200 hover:bg-purple-100">
                + Pomieszczenie techniczne
              </button>

              {(params.technical_rooms || []).map((room, idx) => (
                <div key={idx} className="bg-gray-50 p-2 rounded border border-gray-200">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[9px] font-bold text-purple-800 uppercase">{room.room_id}</span>
                    <button onClick={() => {
                      const newRooms = [...params.technical_rooms];
                      newRooms.splice(idx, 1);
                      setParams(prev => ({...prev, technical_rooms: newRooms}));
                    }} className="text-[8px] text-red-500 px-1">X</button>
                  </div>
                  <div className="grid grid-cols-3 gap-1 mb-1">
                    {['width', 'length', 'height'].map(key => (
                      <div key={key} className="flex flex-col">
                        <span className="text-[7px] text-gray-400 uppercase">{key === 'width' ? 'Szer' : key === 'length' ? 'Dł' : 'Wys'}</span>
                        <input type="number" step="0.5" min="2" max="20" value={room[key]} onChange={(e) => {
                          const newRooms = [...params.technical_rooms];
                          newRooms[idx] = {...newRooms[idx], [key]: parseFloat(e.target.value) || 2};
                          setParams(prev => ({...prev, technical_rooms: newRooms}));
                        }} className="p-0.5 border text-[9px] text-center rounded" />
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-1">
                    <select value={room.position_anchor} onChange={(e) => {
                      const newRooms = [...params.technical_rooms];
                      newRooms[idx] = {...newRooms[idx], position_anchor: e.target.value};
                      setParams(prev => ({...prev, technical_rooms: newRooms}));
                    }} className="flex-1 p-0.5 border text-[8px] rounded">
                      <option value="corner_left_front">Lewy-przód</option>
                      <option value="corner_right_front">Prawy-przód</option>
                      <option value="corner_left_back">Lewy-tył</option>
                      <option value="corner_right_back">Prawy-tył</option>
                      <option value="custom">Własna pozycja</option>
                    </select>
                    <select value={room.fire_rating} onChange={(e) => {
                      const newRooms = [...params.technical_rooms];
                      newRooms[idx] = {...newRooms[idx], fire_rating: e.target.value};
                      setParams(prev => ({...prev, technical_rooms: newRooms}));
                    }} className="w-16 p-0.5 border text-[8px] rounded">
                      <option value="REI60">REI60</option>
                      <option value="REI120">REI120</option>
                      <option value="REI240">REI240</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="8. Biura Zewnętrzne">
            <div className="flex flex-col gap-2">
              <button onClick={() => {
                const newOffice = {
                  office_id: `ext_office_${(params.external_offices || []).length + 1}`,
                  width: 8, length: 24, floor_height: 3.3, num_floors: 2,
                  attached_wall: 'right', position_along_wall: 0,
                  fire_separation: 'REI60', has_windows: true, window_ratio: 0.4
                };
                setParams(prev => ({...prev, external_offices: [...(prev.external_offices || []), newOffice]}));
              }} className="w-full py-1.5 bg-amber-50 text-amber-700 text-[10px] font-bold rounded border border-amber-200 hover:bg-amber-100">
                + Biuro zewnętrzne
              </button>

              {(params.external_offices || []).map((office, idx) => (
                <div key={idx} className="bg-gray-50 p-2 rounded border border-gray-200">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[9px] font-bold text-amber-800 uppercase">{office.office_id}</span>
                    <button onClick={() => {
                      const arr = [...params.external_offices];
                      arr.splice(idx, 1);
                      setParams(prev => ({...prev, external_offices: arr}));
                    }} className="text-[8px] text-red-500 px-1">X</button>
                  </div>
                  <div className="grid grid-cols-2 gap-1 mb-1">
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Głębokość [m]</span>
                      <input type="number" step="1" min="4" max="16" value={office.width} onChange={(e) => {
                        const arr = [...params.external_offices];
                        arr[idx] = {...arr[idx], width: parseFloat(e.target.value) || 8};
                        setParams(prev => ({...prev, external_offices: arr}));
                      }} className="p-0.5 border text-[9px] text-center rounded" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Długość [m]</span>
                      <input type="number" step="1" min="6" max="80" value={office.length} onChange={(e) => {
                        const arr = [...params.external_offices];
                        arr[idx] = {...arr[idx], length: parseFloat(e.target.value) || 24};
                        setParams(prev => ({...prev, external_offices: arr}));
                      }} className="p-0.5 border text-[9px] text-center rounded" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Kondygnacje</span>
                      <input type="number" step="1" min="1" max="4" value={office.num_floors} onChange={(e) => {
                        const arr = [...params.external_offices];
                        arr[idx] = {...arr[idx], num_floors: parseInt(e.target.value) || 2};
                        setParams(prev => ({...prev, external_offices: arr}));
                      }} className="p-0.5 border text-[9px] text-center rounded" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Pozycja wzdłuż [m]</span>
                      <input type="number" step="1" min="0" max="100" value={office.position_along_wall} onChange={(e) => {
                        const arr = [...params.external_offices];
                        arr[idx] = {...arr[idx], position_along_wall: parseFloat(e.target.value) || 0};
                        setParams(prev => ({...prev, external_offices: arr}));
                      }} className="p-0.5 border text-[9px] text-center rounded" />
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <select value={office.attached_wall} onChange={(e) => {
                      const arr = [...params.external_offices];
                      arr[idx] = {...arr[idx], attached_wall: e.target.value};
                      setParams(prev => ({...prev, external_offices: arr}));
                    }} className="flex-1 p-0.5 border text-[8px] rounded">
                      <option value="left">Lewa</option>
                      <option value="right">Prawa</option>
                      <option value="front">Przód</option>
                      <option value="back">Tył</option>
                    </select>
                    <select value={office.fire_separation} onChange={(e) => {
                      const arr = [...params.external_offices];
                      arr[idx] = {...arr[idx], fire_separation: e.target.value};
                      setParams(prev => ({...prev, external_offices: arr}));
                    }} className="w-16 p-0.5 border text-[8px] rounded">
                      <option value="REI60">REI60</option>
                      <option value="REI120">REI120</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="9. Antresole Wewnętrzne">
            <div className="flex flex-col gap-2">
              <button onClick={() => {
                const newMez = {
                  office_id: `mez_${(params.internal_offices || []).length + 1}`,
                  width: 18, length: 12, floor_height: 3.0, num_floors: 2,
                  position_x: 0, position_z: 0, fire_separation: 'REI60',
                  column_grid_x: 6, column_grid_z: 6, has_stairs_internal: true
                };
                setParams(prev => ({...prev, internal_offices: [...(prev.internal_offices || []), newMez]}));
              }} className="w-full py-1.5 bg-indigo-50 text-indigo-700 text-[10px] font-bold rounded border border-indigo-200 hover:bg-indigo-100">
                + Antresola
              </button>

              {(params.internal_offices || []).map((mez, idx) => (
                <div key={idx} className="bg-gray-50 p-2 rounded border border-gray-200">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[9px] font-bold text-indigo-800 uppercase">{mez.office_id}</span>
                    <button onClick={() => {
                      const arr = [...params.internal_offices];
                      arr.splice(idx, 1);
                      setParams(prev => ({...prev, internal_offices: arr}));
                    }} className="text-[8px] text-red-500 px-1">X</button>
                  </div>
                  <div className="grid grid-cols-3 gap-1 mb-1">
                    {[{k:'width',l:'Szer'},{k:'length',l:'Dł'},{k:'num_floors',l:'Kond.'}].map(f => (
                      <div key={f.k} className="flex flex-col">
                        <span className="text-[7px] text-gray-400 uppercase">{f.l}</span>
                        <input type="number" step={f.k === 'num_floors' ? "1" : "1"} min={f.k === 'num_floors' ? 1 : 6} max={f.k === 'num_floors' ? 4 : 60} value={mez[f.k]} onChange={(e) => {
                          const arr = [...params.internal_offices];
                          arr[idx] = {...arr[idx], [f.k]: parseFloat(e.target.value) || 1};
                          setParams(prev => ({...prev, internal_offices: arr}));
                        }} className="p-0.5 border text-[9px] text-center rounded" />
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-1 mb-1">
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Pozycja X [m]</span>
                      <input type="number" step="1" value={mez.position_x} onChange={(e) => {
                        const arr = [...params.internal_offices];
                        arr[idx] = {...arr[idx], position_x: parseFloat(e.target.value) || 0};
                        setParams(prev => ({...prev, internal_offices: arr}));
                      }} className="p-0.5 border text-[9px] text-center rounded" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Pozycja Z [m]</span>
                      <input type="number" step="1" value={mez.position_z} onChange={(e) => {
                        const arr = [...params.internal_offices];
                        arr[idx] = {...arr[idx], position_z: parseFloat(e.target.value) || 0};
                        setParams(prev => ({...prev, internal_offices: arr}));
                      }} className="p-0.5 border text-[9px] text-center rounded" />
                    </div>
                  </div>
                  <select value={mez.fire_separation} onChange={(e) => {
                    const arr = [...params.internal_offices];
                    arr[idx] = {...arr[idx], fire_separation: e.target.value};
                    setParams(prev => ({...prev, internal_offices: arr}));
                  }} className="w-full p-0.5 border text-[8px] rounded">
                    <option value="none">Bez wydzielenia</option>
                    <option value="REI60">REI60</option>
                    <option value="REI120">REI120</option>
                  </select>
                  {mez.num_floors * (mez.floor_height || 3) > params.clear_height && (
                    <div className="mt-1 text-[8px] text-red-600 font-bold">Uwaga: antresola przekracza clear_height!</div>
                  )}
                </div>
              ))}
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="10. Rezerwa pod Biura (Dach)">
            <div className="flex flex-col gap-2">
              <button onClick={() => {
                const numBays = Math.max(1, Math.round(params.length / params.bay_spacing));
                const newZone = {
                  zone_id: `reserve_${(params.office_reserve_zones || []).length + 1}`,
                  start_bay_index: 2, end_bay_index: Math.min(4, numBays - 1),
                  start_axis_index: 0, end_axis_index: 1,
                  roof_type_override: null, truss_fire_rating: 'R60',
                  purlin_doubling_gap: 0.30, separate_drainage: false
                };
                setParams(prev => ({...prev, office_reserve_zones: [...(prev.office_reserve_zones || []), newZone]}));
              }} className="w-full py-1.5 bg-yellow-50 text-yellow-700 text-[10px] font-bold rounded border border-yellow-200 hover:bg-yellow-100">
                + Strefa rezerwy
              </button>

              {(params.office_reserve_zones || []).map((zone, idx) => (
                <div key={idx} className="bg-yellow-50/50 p-2 rounded border border-yellow-200">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[9px] font-bold text-yellow-800 uppercase">{zone.zone_id}</span>
                    <button onClick={() => {
                      const arr = [...params.office_reserve_zones];
                      arr.splice(idx, 1);
                      setParams(prev => ({...prev, office_reserve_zones: arr}));
                    }} className="text-[8px] text-red-500 px-1">X</button>
                  </div>
                  <div className="grid grid-cols-2 gap-1 mb-1">
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Przęsło od</span>
                      <input type="number" step="1" min="0" max={Math.max(1, Math.round(params.length / params.bay_spacing)) - 1} value={zone.start_bay_index} onChange={(e) => {
                        const arr = [...params.office_reserve_zones];
                        arr[idx] = {...arr[idx], start_bay_index: parseInt(e.target.value) || 0};
                        setParams(prev => ({...prev, office_reserve_zones: arr}));
                      }} className="p-0.5 border text-[9px] text-center rounded" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Przęsło do</span>
                      <input type="number" step="1" min="0" max={Math.max(1, Math.round(params.length / params.bay_spacing)) - 1} value={zone.end_bay_index} onChange={(e) => {
                        const arr = [...params.office_reserve_zones];
                        arr[idx] = {...arr[idx], end_bay_index: parseInt(e.target.value) || 0};
                        setParams(prev => ({...prev, office_reserve_zones: arr}));
                      }} className="p-0.5 border text-[9px] text-center rounded" />
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <select value={zone.truss_fire_rating} onChange={(e) => {
                      const arr = [...params.office_reserve_zones];
                      arr[idx] = {...arr[idx], truss_fire_rating: e.target.value};
                      setParams(prev => ({...prev, office_reserve_zones: arr}));
                    }} className="flex-1 p-0.5 border text-[8px] rounded">
                      <option value="R30">R30</option>
                      <option value="R60">R60</option>
                      <option value="R120">R120</option>
                    </select>
                    <div className="flex flex-col">
                      <span className="text-[7px] text-gray-400">Gap [m]</span>
                      <input type="number" step="0.05" min="0.15" max="0.60" value={zone.purlin_doubling_gap} onChange={(e) => {
                        const arr = [...params.office_reserve_zones];
                        arr[idx] = {...arr[idx], purlin_doubling_gap: parseFloat(e.target.value) || 0.30};
                        setParams(prev => ({...prev, office_reserve_zones: arr}));
                      }} className="w-14 p-0.5 border text-[9px] text-center rounded" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        </div>
      )}

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
                  frame_orientation: 0,
                  position_x: (idx - 1) * 35, position_z: 0,
                };
                setParams(prev => ({...prev, blocks: [...(prev.blocks || []), newBlock]}));
              }} className="w-full py-2 bg-green-50 text-green-700 text-[10px] font-bold rounded border border-green-200 hover:bg-green-100">
                + Dodaj Moduł
              </button>

              {(params.blocks || []).map((block, idx) => {
                const isSelected = block.block_id === params._selectedModuleId;
                return (
                <div key={block.block_id} className={`p-2 rounded border ${isSelected ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-gray-50'}`}
                  onClick={() => setParams(prev => ({...prev, _selectedModuleId: block.block_id}))}>
                  <div className="flex justify-between items-center mb-1">
                    <input type="text" value={block.block_id}
                      onChange={(e) => {
                        const newBlocks = [...params.blocks];
                        newBlocks[idx] = {...newBlocks[idx], block_id: e.target.value};
                        setParams(prev => ({...prev, blocks: newBlocks}));
                      }}
                      onClick={(e) => e.stopPropagation()}
                      className="text-[10px] font-black text-blue-800 uppercase bg-transparent border-b border-transparent hover:border-gray-300 focus:border-blue-400 outline-none w-24" />
                    <button onClick={(e) => {
                      e.stopPropagation();
                      const newBlocks = [...params.blocks];
                      newBlocks.splice(idx, 1);
                      setParams(prev => ({...prev, blocks: newBlocks}));
                    }} className="text-[8px] bg-red-50 text-red-600 px-2 py-0.5 rounded hover:bg-red-100">✕</button>
                  </div>

                  {[
                    {key: 'width', label: 'Szer.', min: 10, max: 180, step: 1, unit: 'm'},
                    {key: 'length', label: 'Dł.', min: 10, max: 360, step: 1, unit: 'm'},
                    {key: 'clear_height', label: 'Wys.', min: 4, max: 18, step: 0.5, unit: 'm'},
                    {key: 'bay_spacing', label: 'Rozstaw', min: 4, max: 12, step: 0.5, unit: 'm'},
                    {key: 'number_of_aisles', label: 'Nawy', min: 1, max: 6, step: 1, unit: ''},
                    {key: 'roof_angle', label: 'Kąt dachu', min: 1, max: 15, step: 0.5, unit: '°'},
                  ].map(f => (
                    <div key={f.key} className="flex items-center gap-1 mb-0.5">
                      <span className="text-[7px] font-bold text-gray-500 uppercase w-12 truncate">{f.label}</span>
                      <input type="range" min={f.min} max={f.max} step={f.step} value={block[f.key] || f.min}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => {
                          const newBlocks = [...params.blocks];
                          const val = f.key === 'number_of_aisles' ? parseInt(e.target.value) : parseFloat(e.target.value);
                          newBlocks[idx] = {...newBlocks[idx], [f.key]: val};
                          setParams(prev => ({...prev, blocks: newBlocks}));
                        }} className="flex-1 h-1 bg-gray-200 rounded accent-blue-600" />
                      <span className="text-[8px] font-mono text-blue-600 w-10 text-right">{block[f.key] || f.min}{f.unit}</span>
                    </div>
                  ))}

                  <div className="flex gap-2 mt-1 border-t border-gray-200 pt-1">
                    <div className="flex-1">
                      <span className="text-[7px] font-bold text-gray-500 uppercase">Orientacja ram</span>
                      <select value={block.frame_orientation || 0}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => {
                          const newBlocks = [...params.blocks];
                          newBlocks[idx] = {...newBlocks[idx], frame_orientation: parseInt(e.target.value)};
                          setParams(prev => ({...prev, blocks: newBlocks}));
                        }} className="w-full p-0.5 border rounded text-[8px]">
                        <option value="0">↕ Wzdłuż szerokości (standard)</option>
                        <option value="90">↔ Wzdłuż długości (obrót 90°)</option>
                      </select>
                    </div>
                    <div className="flex-1">
                      <span className="text-[7px] font-bold text-gray-500 uppercase">Odwodnienie</span>
                      <select value={block.roof_drainage_type || 'gravity'}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => {
                          const newBlocks = [...params.blocks];
                          newBlocks[idx] = {...newBlocks[idx], roof_drainage_type: e.target.value};
                          setParams(prev => ({...prev, blocks: newBlocks}));
                        }} className="w-full p-0.5 border rounded text-[8px]">
                        <option value="gravity">Grawitacyjne</option>
                        <option value="vacuum">Podciśnieniowe</option>
                      </select>
                    </div>
                  </div>

                  {/* --- ROZWIJANE SZCZEGOLY MODULU --- */}
                  <details className="mt-1 border-t border-gray-200 pt-1" onClick={(e) => e.stopPropagation()}>
                    <summary className="text-[8px] font-bold text-indigo-600 cursor-pointer hover:text-indigo-800 select-none">
                      ▸ Szczegóły modułu (doki, obudowa, doświetlenie…)
                    </summary>
                    <div className="mt-1 flex flex-col gap-1.5 pl-1">

                      {/* Strefa dokowa */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <label className="flex items-center gap-1 text-[8px] font-bold text-gray-600">
                          <input type="checkbox" checked={block.dock_zone_enabled || false}
                            onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], dock_zone_enabled: e.target.checked}; setParams(prev => ({...prev, blocks: nb})); }}
                          /> Strefa dokowa
                        </label>
                        {block.dock_zone_enabled && (
                          <div className="mt-1 grid grid-cols-3 gap-1">
                            <div><span className="text-[7px] text-gray-400 block">Strona</span>
                              <select value={block.dock_zone_side || 'left'} onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], dock_zone_side: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }} className="w-full p-0.5 border rounded text-[7px]">
                                <option value="left">Lewa</option><option value="right">Prawa</option><option value="both">Obie</option>
                              </select>
                            </div>
                            <div><span className="text-[7px] text-gray-400 block">Szer.[m]</span>
                              <input type="number" min="6" max="36" step="1" value={block.dock_zone_width || 12}
                                onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], dock_zone_width: parseFloat(e.target.value)||12}; setParams(prev => ({...prev, blocks: nb})); }}
                                className="w-full p-0.5 border rounded text-[7px] text-center" />
                            </div>
                            <div><span className="text-[7px] text-gray-400 block">Nawy dok.</span>
                              <input type="number" min="1" max="3" step="1" value={block.dock_zone_aisles || 1}
                                onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], dock_zone_aisles: parseInt(e.target.value)||1}; setParams(prev => ({...prev, blocks: nb})); }}
                                className="w-full p-0.5 border rounded text-[7px] text-center" />
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Obudowa */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Obudowa</span>
                        <div className="grid grid-cols-2 gap-1">
                          <div>
                            <label className="flex items-center gap-1 text-[7px]">
                              <input type="checkbox" checked={block.has_cladding !== false}
                                onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], has_cladding: e.target.checked}; setParams(prev => ({...prev, blocks: nb})); }}
                              /> Panele ścienne
                            </label>
                          </div>
                          <div>
                            <select value={block.cladding_orientation || 'horizontal'}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], cladding_orientation: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px]">
                              <option value="horizontal">Poziomo</option>
                              <option value="vertical">Pionowo</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Dach - konstrukcja */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Dach</span>
                        <div className="grid grid-cols-2 gap-1">
                          <div><span className="text-[7px] text-gray-400 block">Wys. dźwigara</span>
                            <input type="number" min="0.3" max="2.5" step="0.1" value={block.truss_depth || 0.6}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], truss_depth: parseFloat(e.target.value)||0.6}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px] text-center" />
                          </div>
                          <div><span className="text-[7px] text-gray-400 block">Rozstaw płatwi</span>
                            <input type="number" min="1" max="4" step="0.25" value={block.purlin_spacing || 2.0}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], purlin_spacing: parseFloat(e.target.value)||2.0}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px] text-center" />
                          </div>
                        </div>
                      </div>

                      {/* Doswietlenie i oddymianie */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Doświetlenie</span>
                        <div className="flex flex-col gap-0.5">
                          {(block.roof_lights || []).map((zone, zi) => (
                            <div key={zi} className="text-[7px] text-gray-500">
                              {zone.zone_id}: {(zone.items || []).length} pozycji
                            </div>
                          ))}
                          <button onClick={() => {
                            const nb = [...params.blocks];
                            const existing = nb[idx].roof_lights || [];
                            const newItem = { item_id: `${block.block_id}_${Date.now()}`, item_type: "skylight", width: 2.0, length: 3.0, quantity: 4, vent_count: 0, vent_length: 2.0 };
                            const mainZone = existing.find(z => z.zone_id === "main");
                            if (mainZone) {
                              const updated = existing.map(z => z.zone_id === "main" ? {...z, items: [...(z.items||[]), newItem]} : z);
                              nb[idx] = {...nb[idx], roof_lights: updated};
                            } else {
                              nb[idx] = {...nb[idx], roof_lights: [...existing, { zone_id: "main", items: [newItem] }]};
                            }
                            setParams(prev => ({...prev, blocks: nb}));
                          }} className="text-[7px] bg-cyan-50 text-cyan-700 px-1 py-0.5 rounded border border-cyan-200 hover:bg-cyan-100 self-start">
                            + Świetlik/Pasmo
                          </button>
                          {(block.roof_lights || []).map((zone, zi) => (
                            (zone.items || []).map((item, ii) => (
                              <div key={`${zi}-${ii}`} className="flex items-center gap-1 bg-gray-50 rounded p-0.5">
                                <select value={item.item_type} onChange={(e) => {
                                  const nb = [...params.blocks];
                                  const zones = [...(nb[idx].roof_lights || [])];
                                  const items = [...(zones[zi].items || [])];
                                  items[ii] = {...items[ii], item_type: e.target.value};
                                  zones[zi] = {...zones[zi], items};
                                  nb[idx] = {...nb[idx], roof_lights: zones};
                                  setParams(prev => ({...prev, blocks: nb}));
                                }} className="p-0.5 border rounded text-[7px] flex-1">
                                  <option value="skylight">Świetlik</option>
                                  <option value="smoke_vent">Klapa</option>
                                  <option value="light_strip">Pasmo</option>
                                  <option value="light_strip_with_vents">Pasmo+klapy</option>
                                </select>
                                <input type="number" step="0.5" min="0.5" max="6" value={item.width} onChange={(e) => {
                                  const nb = [...params.blocks]; const zones = [...(nb[idx].roof_lights||[])]; const items = [...(zones[zi].items||[])];
                                  items[ii] = {...items[ii], width: parseFloat(e.target.value)||1}; zones[zi] = {...zones[zi], items}; nb[idx] = {...nb[idx], roof_lights: zones};
                                  setParams(prev => ({...prev, blocks: nb}));
                                }} className="w-8 p-0.5 border rounded text-[7px] text-center" title="Szer" />
                                <input type="number" step="1" min="1" max="400" value={item.length} onChange={(e) => {
                                  const nb = [...params.blocks]; const zones = [...(nb[idx].roof_lights||[])]; const items = [...(zones[zi].items||[])];
                                  items[ii] = {...items[ii], length: parseFloat(e.target.value)||1}; zones[zi] = {...zones[zi], items}; nb[idx] = {...nb[idx], roof_lights: zones};
                                  setParams(prev => ({...prev, blocks: nb}));
                                }} className="w-10 p-0.5 border rounded text-[7px] text-center" title="Dł" />
                                <input type="number" step="1" min="1" max="50" value={item.quantity} onChange={(e) => {
                                  const nb = [...params.blocks]; const zones = [...(nb[idx].roof_lights||[])]; const items = [...(zones[zi].items||[])];
                                  items[ii] = {...items[ii], quantity: parseInt(e.target.value)||1}; zones[zi] = {...zones[zi], items}; nb[idx] = {...nb[idx], roof_lights: zones};
                                  setParams(prev => ({...prev, blocks: nb}));
                                }} className="w-6 p-0.5 border rounded text-[7px] text-center" title="Ilość" />
                                <button onClick={() => {
                                  const nb = [...params.blocks]; const zones = [...(nb[idx].roof_lights||[])]; const items = [...(zones[zi].items||[])];
                                  items.splice(ii, 1); zones[zi] = {...zones[zi], items}; nb[idx] = {...nb[idx], roof_lights: zones};
                                  setParams(prev => ({...prev, blocks: nb}));
                                }} className="text-red-500 text-[7px] px-0.5">✕</button>
                              </div>
                            ))
                          ))}
                        </div>
                      </div>

                      {/* Konstrukcja - słupy i fundamenty */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Konstrukcja</span>
                        <div className="grid grid-cols-2 gap-1">
                          <div><span className="text-[7px] text-gray-400 block">Metoda słupów</span>
                            <select value={block.column_method || 'default'}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], column_method: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px]">
                              <option value="default">Automatyczna</option>
                              <option value="manual">Ręczna</option>
                            </select>
                          </div>
                          <div><span className="text-[7px] text-gray-400 block">Metoda fundam.</span>
                            <select value={block.foundation_method || 'default'}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], foundation_method: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px]">
                              <option value="default">Automatyczna</option>
                              <option value="manual">Ręczna</option>
                            </select>
                          </div>
                          <div><span className="text-[7px] text-gray-400 block">Głęb. fund.[m]</span>
                            <input type="number" min="0.5" max="3" step="0.1" value={block.foundation_depth || 1.0}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], foundation_depth: parseFloat(e.target.value)||1.0}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px] text-center" />
                          </div>
                          <div><span className="text-[7px] text-gray-400 block">Cokół [m]</span>
                            <input type="number" min="0.1" max="0.6" step="0.02" value={block.plinth_top_level || 0.30}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], plinth_top_level: parseFloat(e.target.value)||0.30}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px] text-center" />
                          </div>
                        </div>
                      </div>

                      {/* Panel obudowy - wybor z katalogu */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Panel obudowy</span>
                        <select value={block.cladding_panel_id || 'SP2B_E_PIR_100'}
                          onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], cladding_panel_id: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }}
                          className="w-full p-0.5 border rounded text-[7px]">
                          {Object.entries(catalog || {}).map(([id, p]) => (
                            <option key={id} value={id}>{p.name} {p.thickness}mm ({p.core})</option>
                          ))}
                        </select>
                      </div>

                      {/* Blacha dachowa */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Blacha dachowa</span>
                        <select value={block.roof_sheet_id || 'T85_08'}
                          onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], roof_sheet_id: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }}
                          className="w-full p-0.5 border rounded text-[7px]">
                          {Object.entries(roofSheetCatalog || {}).map(([id, s]) => (
                            <option key={id} value={id}>{s.name} {s.thickness}mm (rozp. {s.span}m)</option>
                          ))}
                        </select>
                      </div>

                      {/* Posadzka */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Posadzka</span>
                        <div className="grid grid-cols-2 gap-1">
                          <div><span className="text-[7px] text-gray-400 block">Grubość [m]</span>
                            <input type="number" min="0.1" max="0.4" step="0.02" value={block.floor_thickness || 0.2}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], floor_thickness: parseFloat(e.target.value)||0.2}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px] text-center" />
                          </div>
                          <div><span className="text-[7px] text-gray-400 block">Podbudowa</span>
                            <select value={block.floor_base_type || 'lean_concrete'}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], floor_base_type: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px]">
                              <option value="lean_concrete">Chudy beton</option>
                              <option value="gravel">Kruszywo</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Bezpieczenstwo pozarowe */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">PPOŻ</span>
                        <div className="grid grid-cols-2 gap-1">
                          <div><span className="text-[7px] text-gray-400 block">Obc. ogniowe [MJ/m²]</span>
                            <input type="number" min="100" max="4000" step="50" value={block.fire_load_qd || 500}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], fire_load_qd: parseFloat(e.target.value)||500}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px] text-center" />
                          </div>
                          <div className="flex items-end pb-0.5">
                            <label className="flex items-center gap-1 text-[7px]">
                              <input type="checkbox" checked={block.has_sprinklers || false}
                                onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], has_sprinklers: e.target.checked}; setParams(prev => ({...prev, blocks: nb})); }}
                              /> Tryskacze
                            </label>
                          </div>
                        </div>
                      </div>

                      {/* Stezenia */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Stężenia</span>
                        <div className="grid grid-cols-2 gap-1">
                          <div>
                            <label className="flex items-center gap-1 text-[7px]">
                              <input type="checkbox" checked={block.bracing_roof !== false}
                                onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], bracing_roof: e.target.checked}; setParams(prev => ({...prev, blocks: nb})); }}
                              /> Stężenia dachowe
                            </label>
                          </div>
                          <div>
                            <select value={block.bracing_type || 'x_cross'}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], bracing_type: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px]">
                              <option value="x_cross">Krzyżowe</option>
                              <option value="portal_frame">Portalowe</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Bramy i doki - uproszczona siatka */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Bramy i Doki</span>
                        <p className="text-[7px] text-gray-400 mb-1">Podaj konfigurację doków jako JSON lub użyj siatki w trybie Simple.</p>
                        <div className="grid grid-cols-3 gap-1">
                          <div><span className="text-[7px] text-gray-400 block">Bram szt.</span>
                            <input type="number" min="0" max="20" step="1" value={block.gates_count || 0}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], gates_count: parseInt(e.target.value)||0}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px] text-center" />
                          </div>
                          <div><span className="text-[7px] text-gray-400 block">Doków szt.</span>
                            <input type="number" min="0" max="30" step="1" value={block.docks_count || 0}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], docks_count: parseInt(e.target.value)||0}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px] text-center" />
                          </div>
                          <div><span className="text-[7px] text-gray-400 block">Strona</span>
                            <select value={block.docks_side || 'left'}
                              onChange={(e) => { const nb = [...params.blocks]; nb[idx] = {...nb[idx], docks_side: e.target.value}; setParams(prev => ({...prev, blocks: nb})); }}
                              className="w-full p-0.5 border rounded text-[7px]">
                              <option value="left">Lewa</option>
                              <option value="right">Prawa</option>
                              <option value="both">Obie</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Pomieszczenia techniczne */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Pomieszczenia techniczne</span>
                        {(block.technical_rooms || []).map((room, ri) => (
                          <div key={ri} className="flex items-center gap-1 mb-0.5 bg-gray-50 rounded p-0.5">
                            <span className="text-[7px] text-gray-600 flex-1">{room.room_id} ({room.width}×{room.length}m)</span>
                            <button onClick={() => {
                              const nb = [...params.blocks]; const rooms = [...(nb[idx].technical_rooms||[])]; rooms.splice(ri, 1);
                              nb[idx] = {...nb[idx], technical_rooms: rooms}; setParams(prev => ({...prev, blocks: nb}));
                            }} className="text-red-500 text-[7px]">✕</button>
                          </div>
                        ))}
                        <button onClick={() => {
                          const nb = [...params.blocks];
                          const rooms = [...(nb[idx].technical_rooms || [])];
                          rooms.push({ room_id: `tech_${rooms.length+1}`, width: 6, length: 8, side: "left", position_along: 0 });
                          nb[idx] = {...nb[idx], technical_rooms: rooms};
                          setParams(prev => ({...prev, blocks: nb}));
                        }} className="text-[7px] bg-gray-100 text-gray-600 px-1 py-0.5 rounded border hover:bg-gray-200 mt-0.5">+ Pomieszczenie</button>
                      </div>

                      {/* Biura zewnetrzne */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Biura zewnętrzne</span>
                        {(block.external_offices || []).map((off, oi) => (
                          <div key={oi} className="flex items-center gap-1 mb-0.5 bg-gray-50 rounded p-0.5">
                            <span className="text-[7px] text-gray-600 flex-1">{off.office_id} ({off.width}×{off.length}m, {off.floors}p.)</span>
                            <button onClick={() => {
                              const nb = [...params.blocks]; const offs = [...(nb[idx].external_offices||[])]; offs.splice(oi, 1);
                              nb[idx] = {...nb[idx], external_offices: offs}; setParams(prev => ({...prev, blocks: nb}));
                            }} className="text-red-500 text-[7px]">✕</button>
                          </div>
                        ))}
                        <button onClick={() => {
                          const nb = [...params.blocks];
                          const offs = [...(nb[idx].external_offices || [])];
                          offs.push({ office_id: `office_${offs.length+1}`, width: 12, length: 24, floors: 2, side: "front", floor_height: 3.3 });
                          nb[idx] = {...nb[idx], external_offices: offs};
                          setParams(prev => ({...prev, blocks: nb}));
                        }} className="text-[7px] bg-gray-100 text-gray-600 px-1 py-0.5 rounded border hover:bg-gray-200 mt-0.5">+ Biuro zewn.</button>
                      </div>

                      {/* Antresole wewnetrzne */}
                      <div className="bg-white rounded p-1 border border-gray-100">
                        <span className="text-[8px] font-bold text-gray-600 block mb-0.5">Antresole wewnętrzne</span>
                        {(block.internal_offices || []).map((off, oi) => (
                          <div key={oi} className="flex items-center gap-1 mb-0.5 bg-gray-50 rounded p-0.5">
                            <span className="text-[7px] text-gray-600 flex-1">{off.office_id} ({off.width}×{off.length}m)</span>
                            <button onClick={() => {
                              const nb = [...params.blocks]; const offs = [...(nb[idx].internal_offices||[])]; offs.splice(oi, 1);
                              nb[idx] = {...nb[idx], internal_offices: offs}; setParams(prev => ({...prev, blocks: nb}));
                            }} className="text-red-500 text-[7px]">✕</button>
                          </div>
                        ))}
                        <button onClick={() => {
                          const nb = [...params.blocks];
                          const offs = [...(nb[idx].internal_offices || [])];
                          offs.push({ office_id: `mezzanine_${offs.length+1}`, width: 10, length: 20, corner: "front_left", floor_height: 3.0 });
                          nb[idx] = {...nb[idx], internal_offices: offs};
                          setParams(prev => ({...prev, blocks: nb}));
                        }} className="text-[7px] bg-gray-100 text-gray-600 px-1 py-0.5 rounded border hover:bg-gray-200 mt-0.5">+ Antresola</button>
                      </div>

                    </div>
                  </details>
                </div>
              );})}
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
            <div className="flex flex-col gap-1">
              {(params.module_connections || []).length === 0 && (
                <p className="text-[9px] text-gray-400 italic">Przesuwaj moduły na rzucie aby stworzyć styki. Kliknij na styk aby zmienić typ połączenia.</p>
              )}
              {(params.module_connections || []).map((conn, ci) => {
                const modA = (params.blocks || [])[conn.moduleA];
                const modB = (params.blocks || [])[conn.moduleB];
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
                        const newConns = [...(params.module_connections || [])];
                        newConns[ci] = {...newConns[ci], type: e.target.value};
                        setParams(prev => ({...prev, module_connections: newConns}));
                      }} className="w-full p-0.5 border rounded text-[8px] mb-1">
                      <option value="expansion_joint">Dylatacja (bez ściany wewn.)</option>
                      {!perpendicular && <option value="none">Bez ściany (scalone)</option>}
                      <option value="internal_wall">Ściana wewn. (bez odporności ogn.)</option>
                      <option value="fire_wall">Ściana PPOŻ</option>
                    </select>
                    {conn.type === 'fire_wall' && (
                      <select value={conn.rei_class || 'REI60'}
                        onChange={(e) => {
                          const newConns = [...(params.module_connections || [])];
                          newConns[ci] = {...newConns[ci], rei_class: e.target.value};
                          setParams(prev => ({...prev, module_connections: newConns}));
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
                      {conn.type === 'none' && '→ Moduły scalone: wspólna przestrzeń, brak ściany'}
                      {conn.type === 'internal_wall' && '→ Ściana działowa bez odporności ogniowej'}
                      {conn.type === 'fire_wall' && `→ Ściana PPOŻ ${conn.rei_class || 'REI60'} wystająca ≥0.3m ponad dach`}
                    </p>
                  </div>
                );
              })}
            </div>
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
