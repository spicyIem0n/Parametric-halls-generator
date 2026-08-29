import React from 'react';

/**
 * ExternalOfficesSection — add/edit/remove external office modules.
 * @param {object} data - fields: external_offices
 * @param {function} onChange - (updates) => void
 */
const ExternalOfficesSection = ({ data, onChange }) => {
  const offices = data.external_offices || [];

  const updateOffices = (newArr) => onChange({ external_offices: newArr });

  return (
    <div className="flex flex-col gap-2">
      <button onClick={() => {
        const newOffice = {
          office_id: `ext_office_${offices.length + 1}`,
          width: 8, length: 24, floor_height: 3.3, num_floors: 2,
          attached_wall: 'right', position_along_wall: 0,
          fire_separation: 'REI60', has_windows: true, window_ratio: 0.4
        };
        updateOffices([...offices, newOffice]);
      }} className="w-full py-1.5 bg-amber-50 text-amber-700 text-[10px] font-bold rounded border border-amber-200 hover:bg-amber-100">
        + Biuro zewnętrzne
      </button>

      {offices.map((office, idx) => (
        <div key={idx} className="bg-gray-50 p-2 rounded border border-gray-200">
          <div className="flex justify-between items-center mb-1">
            <span className="text-[9px] font-bold text-amber-800 uppercase">{office.office_id}</span>
            <button onClick={() => {
              const arr = [...offices];
              arr.splice(idx, 1);
              updateOffices(arr);
            }} className="text-[8px] text-red-500 px-1">X</button>
          </div>
          <div className="grid grid-cols-2 gap-1 mb-1">
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Głębokość [m]</span>
              <input type="number" step="1" min="4" max="16" value={office.width} onChange={(e) => {
                const arr = [...offices];
                arr[idx] = { ...arr[idx], width: parseFloat(e.target.value) || 8 };
                updateOffices(arr);
              }} className="p-0.5 border text-[9px] text-center rounded" />
            </div>
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Długość [m]</span>
              <input type="number" step="1" min="6" max="80" value={office.length} onChange={(e) => {
                const arr = [...offices];
                arr[idx] = { ...arr[idx], length: parseFloat(e.target.value) || 24 };
                updateOffices(arr);
              }} className="p-0.5 border text-[9px] text-center rounded" />
            </div>
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Kondygnacje</span>
              <input type="number" step="1" min="1" max="4" value={office.num_floors} onChange={(e) => {
                const arr = [...offices];
                arr[idx] = { ...arr[idx], num_floors: parseInt(e.target.value) || 2 };
                updateOffices(arr);
              }} className="p-0.5 border text-[9px] text-center rounded" />
            </div>
            <div className="flex flex-col">
              <span className="text-[7px] text-gray-400">Pozycja wzdłuż [m]</span>
              <input type="number" step="1" min="0" max="100" value={office.position_along_wall} onChange={(e) => {
                const arr = [...offices];
                arr[idx] = { ...arr[idx], position_along_wall: parseFloat(e.target.value) || 0 };
                updateOffices(arr);
              }} className="p-0.5 border text-[9px] text-center rounded" />
            </div>
          </div>
          <div className="flex gap-1">
            <select value={office.attached_wall} onChange={(e) => {
              const arr = [...offices];
              arr[idx] = { ...arr[idx], attached_wall: e.target.value };
              updateOffices(arr);
            }} className="flex-1 p-0.5 border text-[8px] rounded">
              <option value="left">Lewa</option>
              <option value="right">Prawa</option>
              <option value="front">Przód</option>
              <option value="back">Tył</option>
            </select>
            <select value={office.fire_separation} onChange={(e) => {
              const arr = [...offices];
              arr[idx] = { ...arr[idx], fire_separation: e.target.value };
              updateOffices(arr);
            }} className="w-16 p-0.5 border text-[8px] rounded">
              <option value="REI60">REI60</option>
              <option value="REI120">REI120</option>
            </select>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ExternalOfficesSection;
