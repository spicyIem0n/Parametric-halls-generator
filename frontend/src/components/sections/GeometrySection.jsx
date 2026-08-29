import React from 'react';

/**
 * GeometrySection — wymiary hali, nawy, rozstaw ram.
 * Shared between Simple mode (data=params) and Complex mode (data=block).
 * @param {object} data - object with fields: width, length, clear_height, number_of_aisles, bay_spacing
 * @param {function} onChange - (updates) => void, where updates is {field: value}
 */
const GeometrySection = ({ data, onChange }) => {
  const fields = [
    { name: 'width', label: 'Szerokość [m]', min: 10, max: 180, step: "1" },
    { name: 'length', label: 'Długość [m]', min: 10, max: 360, step: "1" },
    { name: 'clear_height', label: 'Wys. w świetle [m]', min: 4, max: 18, step: "0.5" },
    { name: 'number_of_aisles', label: 'Ilość naw [szt]', min: 1, max: 12, step: "1" },
    { name: 'bay_spacing', label: 'Rozstaw ram [m]', min: 4, max: 12, step: "0.5" },
  ];

  const handleField = (name, value) => {
    const isInt = name === 'number_of_aisles';
    const parsed = isInt ? parseInt(value) : parseFloat(value);
    if (Number.isFinite(parsed)) onChange({ [name]: parsed });
  };

  return (
    <div className="flex flex-col gap-3">
      {fields.map(f => (
        <div key={f.name} className="flex flex-col">
          <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
            <label>{f.label}</label>
            <input type="number" min={f.min} max={f.max} step={f.step}
              value={data[f.name] || f.min}
              onChange={(e) => handleField(f.name, e.target.value)}
              className="w-14 text-right text-blue-600 font-bold bg-transparent border-b border-blue-200 focus:outline-none text-[10px]" />
          </div>
          <input type="range" min={f.min} max={f.max} step={f.step}
            value={data[f.name] || f.min}
            onChange={(e) => handleField(f.name, e.target.value)}
            className="w-full h-1 bg-gray-200 rounded accent-blue-600" />
        </div>
      ))}
    </div>
  );
};

export default GeometrySection;
