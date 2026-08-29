import React from 'react';

/**
 * FireSafetySection — fire load, sprinklers, classification, fire walls (ŚOP).
 * @param {object} data - fields: fire_load_qd, has_sprinklers, fire_walls, length, bay_spacing
 * @param {function} onChange - (updates) => void
 */
const FireSafetySection = ({ data, onChange }) => {
  const fireWalls = data.fire_walls || [];
  const numBays = Math.max(1, Math.round((data.length || 60) / (data.bay_spacing || 6)));
  const qd = data.fire_load_qd || 500;

  const getFireClass = (qd) => {
    if (qd <= 500) return 'Klasa E — brak wymogów';
    if (qd <= 1000) return 'Klasa D — R30 (konstrukcja główna)';
    if (qd <= 2000) return 'Klasa C — R60 / EI60';
    if (qd <= 4000) return 'Klasa B — R120 / EI120';
    return 'Klasa A — R240 / EI240';
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col">
        <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
          <label>Obciążenie ogniowe Qd [MJ/m²]</label>
          <span className="text-red-600">{qd}</span>
        </div>
        <input type="range" min="100" max="5000" step="100"
          value={qd}
          onChange={(e) => onChange({ fire_load_qd: parseFloat(e.target.value) })}
          className="w-full h-1 bg-red-200 rounded accent-red-600" />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase text-gray-500">Instalacja tryskaczowa</span>
        <input type="checkbox" checked={data.has_sprinklers || false}
          onChange={(e) => onChange({ has_sprinklers: e.target.checked })}
          className="rounded" />
      </div>

      <div className="bg-red-50 border border-red-200 rounded p-2 mt-1">
        <span className="text-[9px] font-bold text-red-800 uppercase block mb-1">Klasyfikacja automatyczna</span>
        <span className="text-[10px] text-red-700">{getFireClass(qd)}</span>
      </div>

      <div className="border-t border-red-200 pt-2 mt-2">
        <div className="flex justify-between items-center mb-2">
          <span className="text-[9px] font-bold text-red-800 uppercase">Ściany oddzielenia (ŚOP)</span>
          <button onClick={() => {
            const midAxis = Math.min(Math.floor(numBays / 2), numBays);
            const newFW = { axis_index: midAxis, rei_class: 'REI120', top_type: 'parapet_above_roof' };
            onChange({ fire_walls: [...fireWalls, newFW] });
          }} className="text-[8px] bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200">+ ŚOP</button>
        </div>
        {fireWalls.map((fw, idx) => (
          <div key={idx} className="flex gap-1 items-center mb-1 bg-white p-1 rounded border border-red-100">
            <span className="text-[8px] font-bold text-gray-500 w-8">Oś</span>
            <input type="number" min="1" max={numBays - 1} value={fw.axis_index}
              onChange={(e) => {
                const newFW = [...fireWalls];
                newFW[idx] = { ...newFW[idx], axis_index: parseInt(e.target.value) || 1 };
                onChange({ fire_walls: newFW });
              }} className="w-10 p-0.5 border text-[9px] text-center rounded" />
            <select value={fw.rei_class} onChange={(e) => {
              const newFW = [...fireWalls];
              newFW[idx] = { ...newFW[idx], rei_class: e.target.value };
              onChange({ fire_walls: newFW });
            }} className="flex-1 p-0.5 border text-[8px] rounded">
              <option value="REI60">REI60</option>
              <option value="REI120">REI120</option>
              <option value="REI240">REI240</option>
            </select>
            <select value={fw.top_type} onChange={(e) => {
              const newFW = [...fireWalls];
              newFW[idx] = { ...newFW[idx], top_type: e.target.value };
              onChange({ fire_walls: newFW });
            }} className="flex-1 p-0.5 border text-[8px] rounded">
              <option value="parapet_above_roof">Attyka</option>
              <option value="non_combustible_strip">Pas dachu</option>
            </select>
            <button onClick={() => {
              const newFW = [...fireWalls];
              newFW.splice(idx, 1);
              onChange({ fire_walls: newFW });
            }} className="text-[8px] text-red-500 px-1">X</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FireSafetySection;
