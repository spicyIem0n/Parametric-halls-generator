import React, { useState } from 'react';

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
  // Obliczamy ile pól (slotów) o szerokości ok 4m zmieści się w jednym przęśle
  const slotsPerBay = Math.max(1, Math.floor(params.bay_spacing / 4.0));
  
  const toggleDock = (side, bayIndex, slotIndex) => {
    const key = `${side}-${bayIndex}-${slotIndex}`;
    const current = params.docks_config[key] || 'none';
    let next = current === 'none' ? 'dock' : current === 'dock' ? 'gate' : 'none';

    const newConfig = { ...params.docks_config };
    if (next === 'none') delete newConfig[key];
    else newConfig[key] = next;
    
    setParams({ ...params, docks_config: newConfig });
  };

  const fillSide = (side) => {
    const newConfig = { ...params.docks_config };
    for (let i = 0; i < numBays; i++) {
      for (let k = 0; k < slotsPerBay; k++) newConfig[`${side}-${i}-${k}`] = 'dock';
    }
    setParams({ ...params, docks_config: newConfig });
  };

  const clearSide = (side) => {
    const newConfig = { ...params.docks_config };
    for (let i = 0; i < numBays; i++) {
      for (let k = 0; k < slotsPerBay; k++) delete newConfig[`${side}-${i}-${k}`];
    }
    setParams({ ...params, docks_config: newConfig });
  };

  return (
    <div className="bg-white rounded border border-gray-200 p-2 shadow-sm">
      <div className="flex justify-between mb-2">
        <div className="flex gap-1 flex-col">
           <button onClick={() => fillSide('left')} className="text-[8px] bg-blue-50 text-blue-600 px-1 py-1 rounded">Max Doki L</button>
           <button onClick={() => clearSide('left')} className="text-[8px] bg-red-50 text-red-600 px-1 py-1 rounded">Czyść L</button>
        </div>
        <div className="flex gap-1 flex-col">
           <button onClick={() => fillSide('right')} className="text-[8px] bg-blue-50 text-blue-600 px-1 py-1 rounded">Max Doki R</button>
           <button onClick={() => clearSide('right')} className="text-[8px] bg-red-50 text-red-600 px-1 py-1 rounded">Czyść R</button>
        </div>
      </div>
      
      <div className="flex justify-between gap-2">
        {['left', 'right'].map((side) => (
          <div key={side} className="flex-1 flex flex-col gap-1">
            <span className="text-[9px] font-bold text-center text-gray-400 uppercase">{side === 'left' ? 'LEWA' : 'PRAWA'}</span>
            {[...Array(numBays)].map((_, i) => (
              <div key={`${side}-bay-${i}`} className="flex gap-1 border border-dashed border-gray-300 p-1 rounded bg-gray-50">
                {[...Array(slotsPerBay)].map((_, k) => {
                  const val = params.docks_config[`${side}-${i}-${k}`];
                  return (
                    <button key={`${side}-${i}-${k}`} onClick={() => toggleDock(side, i, k)}
                      className={`flex-1 h-6 rounded text-[7px] border font-bold flex items-center justify-center
                        ${val === 'dock' ? 'bg-blue-500 text-white' : val === 'gate' ? 'bg-orange-500 text-white' : 'bg-white text-gray-400'}`}>
                      {val === 'dock' ? 'DOK' : val === 'gate' ? 'BRM' : '-'}
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


const Controls = ({ params, setParams, onGenerate, isLoading, onPanelChange, catalog }) => {
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setParams(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : parseFloat(value) }));
  };

  return (
    <div className="w-80 bg-white p-4 shadow-xl h-full flex flex-col z-10 relative">
      <h2 className="text-lg font-black text-gray-800 mb-3 border-b pb-2 text-center uppercase">Vibe Hall Builder</h2>

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
                { name: 'width', label: 'Szerokość [m]', min: 10, max: 60, step: "1" },
                { name: 'length', label: 'Długość [m]', min: 10, max: 120, step: "1" },
                { name: 'clear_height', label: 'Wys. w świetle [m]', min: 4, max: 18, step: "0.5" },
                { name: 'number_of_aisles', label: 'Ilość naw [szt]', min: 1, max: 4, step: "1" },
                { name: 'bay_spacing', label: 'Rozstaw ram [m]', min: 4, max: 12, step: "0.5" }
              ].map(f => (
                <div key={f.name} className="flex flex-col">
                  <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                    <label>{f.label}</label> <span className="text-blue-600">{params[f.name]}</span>
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
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="3. Logistyka i Doki" defaultOpen={true}>
            <DockGridSelector params={params} setParams={setParams} />
          </CollapsibleSection>

          <CollapsibleSection title="4. Obudowa Ruukki">
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
          </CollapsibleSection>
<CollapsibleSection title="5. Konstrukcja i Fundamenty">
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
                    {Object.keys(params.manual_column_sections).map(type => (
                      <div key={type} className="flex flex-col gap-1">
                        <label className="text-[8px] font-bold text-gray-500 uppercase">{type.replace('_', ' ')}</label>
                        <div className="flex gap-1">
                          {params.manual_column_sections[type].map((v, i) => (
                            <input key={i} type="number" step="0.05" value={v} onChange={(e) => {
                              const newParams = { ...params };
                              newParams.manual_column_sections[type][i] = parseFloat(e.target.value);
                              setParams(newParams);
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
                    {Object.keys(params.manual_sizes).map(type => (
                      <div key={type} className="flex flex-col gap-1">
                        <label className="text-[8px] font-bold text-gray-500 uppercase">{type.replace('_', ' ')}</label>
                        <div className="flex gap-1">
                          {params.manual_sizes[type].map((v, i) => (
                            <input key={i} type="number" step="0.1" value={v} onChange={(e) => {
                              const newParams = { ...params };
                              newParams.manual_sizes[type][i] = parseFloat(e.target.value);
                              setParams(newParams);
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
        </div>
      )}

      <button onClick={onGenerate} disabled={isLoading || params.hall_type === 'complex'} 
        className="mt-3 w-full py-3 rounded-lg text-white font-black uppercase tracking-widest text-[11px] bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300">
        {isLoading ? 'Przeliczanie...' : 'Buduj Model 3D'}
      </button>
    </div>
  );
};

export default Controls;