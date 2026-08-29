import React from 'react';

/**
 * InternalOfficesSection — add/edit/remove internal mezzanines.
 * @param {object} data - fields: internal_offices, clear_height
 * @param {function} onChange - (updates) => void
 */
const InternalOfficesSection = ({ data, onChange }) => {
  const mezzanines = data.internal_offices || [];

  const updateMezzanines = (newArr) => onChange({ internal_offices: newArr });

  return (
    <div className="flex flex-col gap-2">
      <button onClick={() => {
        const newMez = {
          office_id: `mez_${mezzanines.length + 1}`,
          width: 18, length: 12, floor_height: 3.0, num_floors: 2,
          position_x: 0, position_z: 0, fire_separation: 'REI60',
          column_grid_x: 6, column_grid_z: 6, has_stairs_internal: true
        };
        updateMezzanines([...mezzanines, newMez]);
      }} className="w-full py-1.5 bg-indigo-50 text-indigo-700 text-[10px] font-bold rounded border border-indigo-200 hover:bg-indigo-100">
        + Antresola
      </button>

      {mezzanines.map((mez, idx) => (
        <div key={idx} className="bg-gray-50 p-2 rounded border border-gray-200">
          <div className="flex justify-between items-center mb-1">
            <span className="text-[9px] font-bold text-indigo-800 uppercase">{mez.office_id}</span>
            <button onClick={() => {
              const arr = [...mezzanines];
              arr.splice(idx, 1);
              updateMezzanines(arr);
            }} className="text-[8px] text-red-500 px-1">X</button>
          </div>
          <div className="grid grid-cols-3 gap-1 mb-1">
            {[{k:'width',l:'Szer'},{k:'length',l:'Dł'},{k:'num_floors',l:'Kond.'}].map(f => (
              <div key={f.k} className="flex flex-col">
                <span className="text-[7px] text-gray-400 uppercase">{f.l}</span>
                <input type="number" step={f.k === 'num_floors' ? "1" : "1"}
                  min={f.k === 'num_floors' ? 1 : 6} max={f.k === 'num_floors' ? 4 : 60}
                  value={mez[f.k]} onChange={(e) => {
                    const arr = [...mezzanines];
                    arr[idx] = { ...arr[idx], [f.k]: parseFloat(e.target.value) || 1 };
                    updateMezzanines(arr);
                  }} className="p-0.5 border text-[9px] text-center rounded" />
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-1 mb-1">
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Pozycja X [m]</span>
              <input type="number" step="1" value={mez.position_x} onChange={(e) => {
                const arr = [...mezzanines];
                arr[idx] = { ...arr[idx], position_x: parseFloat(e.target.value) || 0 };
                updateMezzanines(arr);
              }} className="p-0.5 border text-[9px] text-center rounded" />
            </div>
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Pozycja Z [m]</span>
              <input type="number" step="1" value={mez.position_z} onChange={(e) => {
                const arr = [...mezzanines];
                arr[idx] = { ...arr[idx], position_z: parseFloat(e.target.value) || 0 };
                updateMezzanines(arr);
              }} className="p-0.5 border text-[9px] text-center rounded" />
            </div>
          </div>
          <select value={mez.fire_separation} onChange={(e) => {
            const arr = [...mezzanines];
            arr[idx] = { ...arr[idx], fire_separation: e.target.value };
            updateMezzanines(arr);
          }} className="w-full p-0.5 border text-[8px] rounded">
            <option value="none">Bez wydzielenia</option>
            <option value="REI60">REI60</option>
            <option value="REI120">REI120</option>
          </select>
          {mez.num_floors * (mez.floor_height || 3) > (data.clear_height || 10) && (
            <div className="mt-1 text-[8px] text-red-600 font-bold">Uwaga: antresola przekracza clear_height!</div>
          )}
        </div>
      ))}
    </div>
  );
};

export default InternalOfficesSection;
