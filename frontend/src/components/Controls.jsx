import React from 'react';

// --- NOWY KOMPONENT: INTERAKTYWNA MAPA DOKÓW ---
const DockGridSelector = ({ params, setParams }) => {
  const numBays = Math.round(params.length / params.bay_spacing);
  
  const toggleDock = (side, bayIndex) => {
    const key = `${side}-${bayIndex}`;
    const current = params.docks_config[key] || 'none';
    let next = 'none';
    
    if (current === 'none') next = 'dock';
    else if (current === 'dock') next = 'gate';
    else next = 'none';

    const newConfig = { ...params.docks_config };
    if (next === 'none') delete newConfig[key];
    else newConfig[key] = next;
    
    setParams({ ...params, docks_config: newConfig });
  };

  const fillSide = (side) => {
    const newConfig = { ...params.docks_config };
    for (let i = 0; i < numBays; i++) {
      newConfig[`${side}-${i}`] = 'dock';
    }
    setParams({ ...params, docks_config: newConfig });
  };

  const clearSide = (side) => {
    const newConfig = { ...params.docks_config };
    for (let i = 0; i < numBays; i++) {
      delete newConfig[`${side}-${i}`];
    }
    setParams({ ...params, docks_config: newConfig });
  };

  return (
    <div className="mt-4 p-3 bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-[10px] font-bold text-gray-700 uppercase tracking-wider">Logistyka i Bramy (Mapa Pól)</h3>
        <div className="flex gap-1">
           <button onClick={() => fillSide('left')} className="text-[8px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 hover:bg-blue-100">Wszystkie L</button>
           <button onClick={() => clearSide('left')} className="text-[8px] bg-red-50 text-red-600 px-1.5 py-0.5 rounded border border-red-100 hover:bg-red-100">Wyczyść L</button>
           <button onClick={() => fillSide('right')} className="text-[8px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 hover:bg-blue-100">Wszystkie R</button>
           <button onClick={() => clearSide('right')} className="text-[8px] bg-red-50 text-red-600 px-1.5 py-0.5 rounded border border-red-100 hover:bg-red-100">Wyczyść R</button>
        </div>
      </div>
      
      <div className="flex justify-between gap-4">
        {/* Lewa Ściana */}
        <div className="flex-1 flex flex-col gap-1">
          <span className="text-[9px] font-bold text-center text-gray-400">LEWA</span>
          {[...Array(numBays)].map((_, i) => (
            <button
              key={`L-${i}`}
              onClick={() => toggleDock('left', i)}
              className={`h-8 rounded text-[9px] border transition-all flex flex-col items-center justify-center font-bold
                ${params.docks_config[`left-${i}`] === 'dock' ? 'bg-blue-500 text-white border-blue-700 shadow-inner' : 
                  params.docks_config[`left-${i}`] === 'gate' ? 'bg-orange-500 text-white border-orange-700 shadow-inner' : 
                  'bg-gray-50 text-gray-400 border-gray-200 hover:border-blue-300'}`}
            >
              <span className="opacity-50 text-[7px]">{i+1}</span>
              {params.docks_config[`left-${i}`] === 'dock' ? 'DOK' : params.docks_config[`left-${i}`] === 'gate' ? 'BRAMA' : 'BRAK'}
            </button>
          ))}
        </div>

        {/* Prawa Ściana */}
        <div className="flex-1 flex flex-col gap-1">
          <span className="text-[9px] font-bold text-center text-gray-400">PRAWA</span>
          {[...Array(numBays)].map((_, i) => (
            <button
              key={`R-${i}`}
              onClick={() => toggleDock('right', i)}
              className={`h-8 rounded text-[9px] border transition-all flex flex-col items-center justify-center font-bold
                ${params.docks_config[`right-${i}`] === 'dock' ? 'bg-blue-500 text-white border-blue-700 shadow-inner' : 
                  params.docks_config[`right-${i}`] === 'gate' ? 'bg-orange-500 text-white border-orange-700 shadow-inner' : 
                  'bg-gray-50 text-gray-400 border-gray-200 hover:border-blue-300'}`}
            >
              <span className="opacity-50 text-[7px]">{i+1}</span>
              {params.docks_config[`right-${i}`] === 'dock' ? 'DOK' : params.docks_config[`right-${i}`] === 'gate' ? 'BRAMA' : 'BRAK'}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};


const Controls = ({ params, setParams, onGenerate, isLoading, onPanelChange, catalog }) => {
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setParams(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : (type === 'number' || type === 'range' ? parseFloat(value) : value) 
    }));
  };

  const handleManualSizeChange = (category, type, index, value) => {
    const newParams = { ...params };
    newParams[category][type][index] = parseFloat(value);
    setParams(newParams);
  };

  return (
    <div className="w-96 bg-white p-6 shadow-lg h-full flex flex-col z-10 relative">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b pb-2 text-center uppercase tracking-tighter">Vibe Hall Builder</h2>

      <div className="flex-1 overflow-y-auto flex flex-col gap-5 pr-2 custom-scrollbar">
        
        {/* TYP HALI */}
        <div className="flex bg-gray-100 rounded-lg p-1 mb-2">
          {['simple', 'complex'].map(type => (
            <button key={type} onClick={() => setParams(prev => ({...prev, hall_type: type}))}
              className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-all uppercase ${params.hall_type === type ? 'bg-white shadow text-blue-600' : 'text-gray-400'}`}>
              {type}
            </button>
          ))}
        </div>

        {params.hall_type === 'simple' && (
          <>
            {/* 1. GEOMETRIA GŁÓWNA */}
            <div className="flex flex-col gap-3">
              <h3 className="text-[11px] font-black text-blue-900 uppercase">1. Geometria Główna</h3>
              {[
                { name: 'width', label: 'Szerokość [m]', min: 10, max: 60, step: "1" },
                { name: 'length', label: 'Długość [m]', min: 10, max: 120, step: "1" },
                { name: 'clear_height', label: 'Wys. w świetle [m]', min: 4, max: 18, step: "0.5" },
                { name: 'number_of_aisles', label: 'Ilość naw [szt]', min: 1, max: 4, step: "1" },
                { name: 'roof_angle', label: 'Kąt dachu [°]', min: 2, max: 35, step: "1" },
                { name: 'bay_spacing', label: 'Rozstaw ram [m]', min: 4, max: 12, step: "0.5" }
              ].map(f => (
                <div key={f.name} className="flex flex-col">
                  <div className="flex justify-between text-[10px] font-bold text-gray-400 uppercase">
                    <label>{f.label}</label>
                    <span className="text-blue-600">{params[f.name]}</span>
                  </div>
                  <input type="range" name={f.name} min={f.min} max={f.max} step={f.step} value={params[f.name]} onChange={handleChange} className="w-full h-1 bg-gray-200 rounded appearance-none accent-blue-600" />
                </div>
              ))}
            </div>

          {/* ODWODNIENIE I DACH */}
              <div className="border-t pt-4">
                <h3 className="text-[11px] font-black text-blue-900 uppercase mb-3">Geometria Dachu</h3>
                
                <div className="flex flex-col gap-3">
                  <label className="text-[10px] font-bold text-gray-500 uppercase">
                    Typ Odwodnienia
                    <select name="roof_drainage_type" value={params.roof_drainage_type} onChange={handleChange} className="w-full mt-1 p-2 border rounded bg-gray-50 text-xs font-bold text-blue-800">
                      <option value="gravity">Grawitacyjne (Dach dwuspadowy)</option>
                      <option value="vacuum">Podciśnieniowe (Dach płaski / Koperty)</option>
                    </select>
                  </label>

                  {params.roof_drainage_type === 'vacuum' ? (
                    <div className="bg-blue-50/50 border border-blue-200 p-3 rounded-lg flex flex-col gap-3">
                      <span className="text-[10px] font-bold text-blue-800 uppercase">Siatka zlewni wewn. (Koperty)</span>
                      
                      <div className="grid grid-cols-2 gap-2">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-bold text-gray-500 uppercase">Ilość w osi X</label>
                          <input type="number" min="1" max="4" name="drainage_zones_x" value={params.drainage_zones_x} onChange={handleChange} className="p-1 border rounded text-center text-xs" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-bold text-gray-500 uppercase">Ilość w osi Z</label>
                          <input type="number" min="1" max="10" name="drainage_zones_z" value={params.drainage_zones_z} onChange={handleChange} className="p-1 border rounded text-center text-xs" />
                        </div>
                      </div>

                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between text-[9px] font-bold text-gray-500 uppercase">
                          <label>Spadek do wpustu [%]</label>
                          <span className="text-blue-600">{params.roof_slope_percent}%</span>
                        </div>
                        <input type="range" name="roof_slope_percent" min="1" max="5" step="0.5" value={params.roof_slope_percent} onChange={handleChange} className="w-full h-1 bg-blue-200 rounded appearance-none" />
                      </div>

                      {/* Kalkulator Zlewni na żywo */}
                      {(() => {
                        const totalArea = params.width * params.length;
                        const numZones = params.drainage_zones_x * params.drainage_zones_z;
                        const areaPerZone = totalArea / numZones;
                        const isOverloaded = areaPerZone > 400;
                        return (
                          <div className={`mt-2 p-2 rounded text-[10px] ${isOverloaded ? 'bg-red-100 text-red-800 border border-red-300' : 'bg-white border border-gray-200 text-gray-600'}`}>
                            <div className="flex justify-between font-bold">
                              <span>Pow. 1 zlewni:</span>
                              <span>{areaPerZone.toFixed(0)} m²</span>
                            </div>
                            {isOverloaded && <span className="block mt-1 text-[9px] font-bold">⚠️ Uwaga: Zlewnia przekracza 400m². Zaleca się dodanie wpustów.</span>}
                          </div>
                        );
                      })()}
                    </div>
                  ) : (
                    <div className="flex flex-col gap-1 mt-2">
                      <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                        <label>Kąt dachu [°]</label>
                        <span className="text-blue-600">{params.roof_angle}</span>
                      </div>
                      <input type="range" name="roof_angle" min="2" max="35" step="1" value={params.roof_angle} onChange={handleChange} className="w-full h-1 bg-gray-200 rounded appearance-none" />
                    </div>
                  )}

                  {/* DODANY SUWAK ROZSTAWU PŁATWI Z POPRZEDNIEJ ITERACJI */}
                  <div className="flex flex-col gap-1 mt-3 pt-3 border-t border-gray-200 border-dashed">
                    <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                      <label>Max. rozstaw płatwi (wg tablic) [m]</label>
                      <span className="text-blue-600">{params.purlin_spacing}</span>
                    </div>
                    <input type="range" name="purlin_spacing" min="1" max="4" step="0.5" value={params.purlin_spacing} onChange={handleChange} className="w-full h-1 bg-gray-200 rounded appearance-none accent-blue-600" />
                  </div>
                </div>
              </div>

            {/* 2. POSADZKA PRZEMYSŁOWA */}
            <div className="border-t pt-4">
              <h3 className="text-[11px] font-black text-blue-900 uppercase mb-3">2. Posadzka (Poziom 0.00)</h3>
              <div className="flex flex-col gap-3">
                <div className="flex flex-col gap-1 text-[10px] font-bold text-gray-500 uppercase">
                  <label>Grubość płyty posadzkowej [m]</label>
                  <input type="number" step="0.05" name="floor_thickness" value={params.floor_thickness} onChange={handleChange} className="p-2 border rounded" />
                </div>
                <div className="flex flex-col gap-1 text-[10px] font-bold text-gray-500 uppercase">
                  <label>Rodzaj podbudowy</label>
                  <select name="floor_base_type" value={params.floor_base_type} onChange={handleChange} className="p-2 border rounded bg-gray-50 text-xs font-bold text-gray-700">
                    <option value="lean_concrete">Chudy beton</option>
                    <option value="cement_stabilized">Grunt stabilizowany cementem</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1 text-[10px] font-bold text-gray-500 uppercase">
                  <label>Grubość podbudowy [m]</label>
                  <input type="number" step="0.05" name="floor_base_thickness" value={params.floor_base_thickness} onChange={handleChange} className="p-2 border rounded" />
                </div>
              </div>
            </div>

            {/* 3. SŁUPY */}
            <div className="border-t pt-4">
              <h3 className="text-[11px] font-black text-blue-900 uppercase mb-3">3. Słupy (Konstrukcja)</h3>
              <select name="column_method" value={params.column_method} onChange={handleChange} className="w-full p-2 border rounded text-xs mb-3 font-bold bg-gray-50">
                <option value="default">Domyślne przekroje</option>
                <option value="manual">Ręczne przekroje [X, Z]</option>
              </select>

              {params.column_method === 'manual' && (
                <div className="bg-gray-50 p-2 rounded flex flex-col gap-3 border border-dashed border-gray-300">
                  {Object.keys(params.manual_column_sections).map(type => (
                    <div key={type} className="flex flex-col gap-1">
                      <label className="text-[9px] font-bold text-gray-500 uppercase">{type.replace('_', ' ')}</label>
                      <div className="flex gap-1">
                        {params.manual_column_sections[type].map((v, i) => (
                          <input key={i} type="number" step="0.01" value={v} onChange={(e) => handleManualSizeChange('manual_column_sections', type, i, e.target.value)} className="w-full p-1 border text-[10px] text-center rounded font-mono" />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 4. FUNDAMENTY & DOKI (ZINTEGROWANA MAPA DOKÓW) */}
            <div className="border-t pt-4">
              <h3 className="text-[11px] font-black text-blue-900 uppercase mb-3">4. Fundamenty & Doki</h3>
              
              {/* NOWY KOMPONENT WYBORU DOKÓW */}
              <DockGridSelector params={params} setParams={setParams} />

              <select name="foundation_method" value={params.foundation_method} onChange={handleChange} className="w-full p-2 border rounded text-xs mb-3 mt-4 font-bold bg-gray-50">
                <option value="default">Gabaryty domyślne</option>
                <option value="manual">Gabaryty ręczne [A, B, H]</option>
              </select>

              {params.foundation_method === 'manual' && (
                <div className="bg-blue-50/50 p-2 rounded flex flex-col gap-3 border border-blue-100 mb-3">
                  {Object.keys(params.manual_sizes).map(type => (
                    <div key={type} className="flex flex-col gap-1">
                      <label className="text-[9px] font-bold text-gray-500 uppercase">{type.replace('_', ' ')}</label>
                      <div className="flex gap-1">
                        {params.manual_sizes[type].map((v, i) => (
                          <input key={i} type="number" step="0.05" value={v} onChange={(e) => handleManualSizeChange('manual_sizes', type, i, e.target.value)} className="w-full p-1 border text-[10px] text-center rounded font-mono" />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex flex-col gap-3 mt-3">
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-gray-400 uppercase">Zagłębienie główne [m]</span>
                  <input type="number" step="0.1" name="foundation_depth" value={params.foundation_depth} onChange={handleChange} className="w-full p-1.5 border rounded text-xs" />
                </div>
                
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-orange-600 uppercase">Zagłębienie dokowe [m]</span>
                  <input type="number" step="0.1" name="dock_foundation_depth" value={params.dock_foundation_depth} onChange={handleChange} className="w-full p-1.5 border border-orange-300 bg-orange-50 rounded text-xs" />
                </div>
                
              </div>
            </div>

            {/* 5. OBUDOWA PŁYTAMI RUUKKI */}
            <div className="border-t pt-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-[11px] font-black text-blue-900 uppercase">5. Obudowa Ruukki</h3>
                <input type="checkbox" name="has_cladding" checked={params.has_cladding} onChange={handleChange} className="w-4 h-4 text-blue-600 rounded" />
              </div>

              {params.has_cladding && (
                <div className="flex flex-col gap-3">
                  <label className="text-[10px] font-bold text-gray-500 uppercase">
                    Układ paneli ściennych
                    <select name="cladding_orientation" value={params.cladding_orientation} onChange={handleChange} className="w-full mt-1 p-2 border rounded bg-gray-50 text-xs font-bold text-gray-700">
                      <option value="horizontal">Poziomy (do słupów)</option>
                      <option value="vertical">Pionowy (do rygli)</option>
                    </select>
                  </label>

                  {/* KARTA KATALOGOWA RUUKKI */}
                  <div className="border border-blue-200 bg-blue-50/30 rounded-lg p-3">
                    <label className="text-[10px] font-bold text-blue-800 uppercase block mb-1">Wybór Płyty Ściennej (Katalog Ruukki)</label>
                    <select value={params.cladding_panel_id} onChange={(e) => onPanelChange(e.target.value)} className="w-full p-2 border border-blue-300 rounded text-xs font-bold text-blue-900 bg-white mb-3 shadow-sm">
                      {Object.entries(catalog).map(([id, panel]) => (
                        <option key={id} value={id}>{panel.name} ({panel.thickness}mm)</option>
                      ))}
                    </select>

                    <div className="grid grid-cols-2 gap-2 text-[10px]">
                      <div className="bg-white p-2 rounded border border-gray-100 shadow-sm flex flex-col justify-center">
                        <span className="block text-gray-400 uppercase text-[8px]">Rdzeń</span>
                        <span className="font-bold text-gray-700">{catalog[params.cladding_panel_id].core}</span>
                      </div>
                      <div className="bg-white p-2 rounded border border-gray-100 shadow-sm flex flex-col justify-center">
                        <span className="block text-gray-400 uppercase text-[8px]">Odporność Ogniowa</span>
                        <span className="font-bold text-red-600">{catalog[params.cladding_panel_id].fire}</span>
                      </div>
                      <div className="bg-white p-2 rounded border border-gray-100 shadow-sm col-span-2 flex justify-between items-center">
                        <div>
                          <span className="block text-gray-400 uppercase text-[8px]">Współczynnik Uc [W/m²K]</span>
                          <span className="font-black text-blue-600 text-lg">{catalog[params.cladding_panel_id].uValue}</span>
                        </div>
                        <div className="text-right">
                          <span className="block text-gray-400 uppercase text-[8px]">Grubość Płyty</span>
                          <span className="font-bold text-gray-700 text-sm">{catalog[params.cladding_panel_id].thickness} mm</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <button onClick={onGenerate} disabled={isLoading || params.hall_type === 'complex'} 
        className={`mt-4 w-full py-4 rounded-xl text-white font-black uppercase tracking-widest transition-all text-xs ${isLoading || params.hall_type === 'complex' ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-200 active:scale-95'}`}>
        {isLoading ? 'Przeliczanie...' : 'Buduj Model 3D'}
      </button>
    </div>
  );
};

export default Controls;