import React, { useState } from 'react';

/**
 * DockGrid — interactive grid for placing docks/gates per bay/slot.
 * Refactored to accept explicit props instead of full params.
 */
const DockGrid = ({ length, baySpacing, docksConfig, onConfigChange }) => {
  const numBays = Math.max(1, Math.round(length / baySpacing));
  const slotsPerBay = Math.max(1, Math.floor(baySpacing / 4.0));
  const [openingType, setOpeningType] = useState("dock");
  const [lastClicked, setLastClicked] = useState(null);

  const flatToKey = (side, flat) => `${side}-${Math.floor(flat / slotsPerBay)}-${flat % slotsPerBay}`;

  const applyToSlot = (side, flatIndex) => {
    const key = flatToKey(side, flatIndex);
    const newConfig = { ...docksConfig };
    if (openingType === "none") delete newConfig[key];
    else newConfig[key] = openingType;
    onConfigChange(newConfig);
  };

  const applyRange = (side, from, to) => {
    const min = Math.min(from, to), max = Math.max(from, to);
    const newConfig = { ...docksConfig };
    for (let f = min; f <= max; f++) {
      const key = flatToKey(side, f);
      if (openingType === "none") delete newConfig[key];
      else newConfig[key] = openingType;
    }
    onConfigChange(newConfig);
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
    const newConfig = { ...docksConfig };
    const fillType = openingType === "none" ? "dock" : openingType;
    for (let i = 0; i < numBays; i++)
      for (let k = 0; k < slotsPerBay; k++) newConfig[`${side}-${i}-${k}`] = fillType;
    onConfigChange(newConfig);
  };

  const clearSide = (side) => {
    const newConfig = { ...docksConfig };
    for (let i = 0; i < numBays; i++)
      for (let k = 0; k < slotsPerBay; k++) delete newConfig[`${side}-${i}-${k}`];
    onConfigChange(newConfig);
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
                  const val = docksConfig[`${side}-${i}-${k}`];
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

/**
 * DocksSection — DockGrid + dock zone configuration.
 * @param {object} data - fields: length, bay_spacing, docks_config, number_of_aisles, dock_zone_enabled, dock_zone_side, dock_zone_width, dock_zone_aisles, width
 * @param {function} onChange - (updates) => void
 */
const DocksSection = ({ data, onChange }) => {
  return (
    <div className="flex flex-col gap-4">
      {/* Interactive dock/gate grid */}
      <DockGrid
        length={data.length || 60}
        baySpacing={data.bay_spacing || 6}
        docksConfig={data.docks_config || {}}
        onConfigChange={(newConfig) => onChange({ docks_config: newConfig })}
      />

      {/* Dock zone (only when multiple aisles) */}
      {(data.number_of_aisles || 1) > 1 && (
        <div className="border-t pt-3 mt-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-gray-500">Strefa dokowa aktywna</span>
            <input type="checkbox" checked={data.dock_zone_enabled || false}
              onChange={(e) => onChange({ dock_zone_enabled: e.target.checked })}
              className="rounded" />
          </div>

          {data.dock_zone_enabled && (
            <div className="flex flex-col gap-2 bg-blue-50/50 p-2 rounded border border-blue-100">
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-gray-500 uppercase mb-1">Strona strefy dokowej</span>
                <select value={data.dock_zone_side || "left"}
                  onChange={(e) => onChange({ dock_zone_side: e.target.value })}
                  className="w-full p-2 border rounded text-[10px] font-bold bg-white">
                  <option value="left">Lewa (strefa po lewej)</option>
                  <option value="right">Prawa (strefa po prawej)</option>
                  <option value="both">Obie strony</option>
                </select>
              </div>

              <div className="flex flex-col">
                <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                  <label>Szer. nawy dokowej [m]</label>
                  <input type="number" min="6" max="24" step="0.5"
                    value={data.dock_zone_width || 12}
                    onChange={(e) => onChange({ dock_zone_width: parseFloat(e.target.value) || 12 })}
                    className="w-14 text-right text-blue-600 font-bold bg-transparent border-b border-blue-200 focus:outline-none text-[10px]" />
                </div>
                <input type="range" min="6" max="24" step="0.5"
                  value={data.dock_zone_width || 12}
                  onChange={(e) => onChange({ dock_zone_width: parseFloat(e.target.value) || 12 })}
                  className="w-full h-1 bg-blue-200 rounded accent-blue-600" />
              </div>

              <div className="flex flex-col">
                <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
                  <label>Ile naw skrajnych w strefie</label>
                  <span className="text-blue-600">{data.dock_zone_aisles || 1}</span>
                </div>
                <input type="range" min="1" max={Math.max(1, (data.number_of_aisles || 2) - 1)} step="1"
                  value={data.dock_zone_aisles || 1}
                  onChange={(e) => onChange({ dock_zone_aisles: parseInt(e.target.value) || 1 })}
                  className="w-full h-1 bg-blue-200 rounded accent-blue-600" />
              </div>

              <div className="text-[9px] text-gray-400 mt-1">
                Nawa dokowa: <span className="text-blue-600 font-bold">{data.dock_zone_width || 12}m</span> |
                Pozostałe nawy: <span className="text-blue-600 font-bold">
                  {((data.width - (data.dock_zone_width || 12) * (data.dock_zone_aisles || 1) * (data.dock_zone_side === "both" ? 2 : 1)) / Math.max(1, (data.number_of_aisles || 2) - (data.dock_zone_aisles || 1) * (data.dock_zone_side === "both" ? 2 : 1))).toFixed(1)}m
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocksSection;
export { DockGrid };
