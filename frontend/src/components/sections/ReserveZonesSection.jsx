import React from 'react';

/**
 * ReserveZonesSection — reserve zones for future office space in roof area.
 * @param {object} data - fields: office_reserve_zones, length, bay_spacing
 * @param {function} onChange - (updates) => void
 */
const ReserveZonesSection = ({ data, onChange }) => {
  const zones = data.office_reserve_zones || [];
  const numBays = Math.max(1, Math.round((data.length || 60) / (data.bay_spacing || 6)));

  const updateZones = (newArr) => onChange({ office_reserve_zones: newArr });

  return (
    <div className="flex flex-col gap-2">
      <button onClick={() => {
        const newZone = {
          zone_id: `reserve_${zones.length + 1}`,
          start_bay_index: 2, end_bay_index: Math.min(4, numBays - 1),
          start_axis_index: 0, end_axis_index: 1,
          roof_type_override: null, truss_fire_rating: 'R60',
          purlin_doubling_gap: 0.30, separate_drainage: false
        };
        updateZones([...zones, newZone]);
      }} className="w-full py-1.5 bg-yellow-50 text-yellow-700 text-[10px] font-bold rounded border border-yellow-200 hover:bg-yellow-100">
        + Strefa rezerwy
      </button>

      {zones.map((zone, idx) => (
        <div key={idx} className="bg-yellow-50/50 p-2 rounded border border-yellow-200">
          <div className="flex justify-between items-center mb-1">
            <span className="text-[9px] font-bold text-yellow-800 uppercase">{zone.zone_id}</span>
            <button onClick={() => {
              const arr = [...zones];
              arr.splice(idx, 1);
              updateZones(arr);
            }} className="text-[8px] text-red-500 px-1">X</button>
          </div>
          <div className="grid grid-cols-2 gap-1 mb-1">
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Przęsło od</span>
              <input type="number" step="1" min="0" max={numBays - 1}
                value={zone.start_bay_index} onChange={(e) => {
                  const arr = [...zones];
                  arr[idx] = { ...arr[idx], start_bay_index: parseInt(e.target.value) || 0 };
                  updateZones(arr);
                }} className="p-0.5 border text-[9px] text-center rounded" />
            </div>
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Przęsło do</span>
              <input type="number" step="1" min="0" max={numBays - 1}
                value={zone.end_bay_index} onChange={(e) => {
                  const arr = [...zones];
                  arr[idx] = { ...arr[idx], end_bay_index: parseInt(e.target.value) || 0 };
                  updateZones(arr);
                }} className="p-0.5 border text-[9px] text-center rounded" />
            </div>
          </div>
          <div className="flex gap-1">
            <select value={zone.truss_fire_rating} onChange={(e) => {
              const arr = [...zones];
              arr[idx] = { ...arr[idx], truss_fire_rating: e.target.value };
              updateZones(arr);
            }} className="flex-1 p-0.5 border text-[8px] rounded">
              <option value="R30">R30</option>
              <option value="R60">R60</option>
              <option value="R120">R120</option>
            </select>
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Gap [m]</span>
              <input type="number" step="0.05" min="0.15" max="0.60"
                value={zone.purlin_doubling_gap} onChange={(e) => {
                  const arr = [...zones];
                  arr[idx] = { ...arr[idx], purlin_doubling_gap: parseFloat(e.target.value) || 0.30 };
                  updateZones(arr);
                }} className="w-14 p-0.5 border text-[9px] text-center rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ReserveZonesSection;
