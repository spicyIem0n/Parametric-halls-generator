import React from 'react';

/**
 * TechnicalRoomsSection — add/edit/remove technical rooms.
 * @param {object} data - fields: technical_rooms
 * @param {function} onChange - (updates) => void
 */
const TechnicalRoomsSection = ({ data, onChange }) => {
  const rooms = data.technical_rooms || [];

  const updateRooms = (newRooms) => onChange({ technical_rooms: newRooms });

  return (
    <div className="flex flex-col gap-2">
      <button onClick={() => {
        const newRoom = {
          room_id: `tech_${rooms.length + 1}`,
          width: 6, length: 4, height: 3,
          position_anchor: 'corner_left_front', position_offset: [0, 0, 0],
          fire_rating: 'REI120', has_own_roof: true, floor_level: 0
        };
        updateRooms([...rooms, newRoom]);
      }} className="w-full py-1.5 bg-purple-50 text-purple-700 text-[10px] font-bold rounded border border-purple-200 hover:bg-purple-100">
        + Pomieszczenie techniczne
      </button>

      {rooms.map((room, idx) => (
        <div key={idx} className="bg-gray-50 p-2 rounded border border-gray-200">
          <div className="flex justify-between items-center mb-1">
            <span className="text-[9px] font-bold text-purple-800 uppercase">{room.room_id}</span>
            <button onClick={() => {
              const arr = [...rooms];
              arr.splice(idx, 1);
              updateRooms(arr);
            }} className="text-[8px] text-red-500 px-1">X</button>
          </div>
          <div className="grid grid-cols-3 gap-1 mb-1">
            {['width', 'length', 'height'].map(key => (
              <div key={key} className="flex flex-col">
                <span className="text-[7px] text-gray-400 uppercase">{key === 'width' ? 'Szer' : key === 'length' ? 'Dł' : 'Wys'}</span>
                <input type="number" step="0.5" min="2" max="20" value={room[key]} onChange={(e) => {
                  const arr = [...rooms];
                  arr[idx] = { ...arr[idx], [key]: parseFloat(e.target.value) || 2 };
                  updateRooms(arr);
                }} className="p-0.5 border text-[9px] text-center rounded" />
              </div>
            ))}
          </div>
          <div className="flex gap-1">
            <select value={room.position_anchor} onChange={(e) => {
              const arr = [...rooms];
              arr[idx] = { ...arr[idx], position_anchor: e.target.value };
              updateRooms(arr);
            }} className="flex-1 p-0.5 border text-[8px] rounded">
              <option value="corner_left_front">Lewy-przód</option>
              <option value="corner_right_front">Prawy-przód</option>
              <option value="corner_left_back">Lewy-tył</option>
              <option value="corner_right_back">Prawy-tył</option>
              <option value="custom">Własna pozycja</option>
            </select>
            <select value={room.fire_rating} onChange={(e) => {
              const arr = [...rooms];
              arr[idx] = { ...arr[idx], fire_rating: e.target.value };
              updateRooms(arr);
            }} className="w-16 p-0.5 border text-[8px] rounded">
              <option value="REI60">REI60</option>
              <option value="REI120">REI120</option>
              <option value="REI240">REI240</option>
            </select>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TechnicalRoomsSection;
