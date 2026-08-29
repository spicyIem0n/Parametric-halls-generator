import React from 'react';

/**
 * RoofSection — typ odwodnienia, kąt dachu, płatwie, blacha, dźwigar.
 * @param {object} data - fields: roof_drainage_type, roof_angle, purlin_spacing, roof_sheet_id, roof_sheet_height, truss_depth, clear_height
 * @param {function} onChange - (updates) => void
 * @param {object} roofSheetCatalog - catalog of roof sheets
 */
const RoofSection = ({ data, onChange, roofSheetCatalog }) => {
  return (
    <div className="flex flex-col gap-3">
      <select value={data.roof_drainage_type || 'gravity'}
        onChange={(e) => onChange({ roof_drainage_type: e.target.value })}
        className="w-full p-2 border rounded bg-gray-50 text-[10px] font-bold">
        <option value="gravity">Grawitacyjne (Dwuspadowy)</option>
        <option value="vacuum">Podciśnieniowe (Koperty)</option>
      </select>

      {data.roof_drainage_type === 'gravity' && (
        <div className="flex flex-col">
          <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
            <label>Kąt dachu [°]</label>
            <span className="text-blue-600">{data.roof_angle || 5}</span>
          </div>
          <input type="range" min="2" max="35" step="1"
            value={data.roof_angle || 5}
            onChange={(e) => onChange({ roof_angle: parseFloat(e.target.value) })}
            className="w-full h-1 bg-gray-200 rounded" />
        </div>
      )}

      <div className="flex flex-col border-t pt-2 mt-2">
        <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
          <label>Max. rozstaw płatwi [m]</label>
          <span className="text-blue-600">{data.purlin_spacing || 2.0}</span>
        </div>
        <input type="range" min="1" max="4" step="0.5"
          value={data.purlin_spacing || 2.0}
          onChange={(e) => onChange({ purlin_spacing: parseFloat(e.target.value) })}
          className="w-full h-1 bg-gray-200 rounded" />
      </div>

      <div className="flex flex-col border-t pt-2 mt-2">
        <span className="text-[10px] font-bold text-gray-500 uppercase mb-1">Blacha trapezowa dachowa</span>
        {roofSheetCatalog && (
          <select value={data.roof_sheet_id || "T85_08"}
            onChange={(e) => {
              const sheet = roofSheetCatalog[e.target.value];
              onChange({ roof_sheet_id: e.target.value, roof_sheet_height: sheet.height / 1000 });
            }}
            className="w-full p-2 border rounded text-[10px] font-bold bg-gray-50">
            {Object.entries(roofSheetCatalog).map(([id, sheet]) => (
              <option key={id} value={id}>{sheet.name} (h={sheet.height}mm, gr={sheet.thickness}mm, rozp. do {sheet.span}m)</option>
            ))}
          </select>
        )}
      </div>

      <div className="flex flex-col border-t pt-2 mt-2">
        <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
          <label>Wys. konstrukcji dachu [m]</label>
          <input type="number" min="0.3" max="2.5" step="0.1"
            value={data.truss_depth || 0.6}
            onChange={(e) => onChange({ truss_depth: parseFloat(e.target.value) || 0.6 })}
            className="w-14 text-right text-blue-600 font-bold bg-transparent border-b border-blue-200 focus:outline-none text-[10px]" />
        </div>
        <input type="range" min="0.3" max="2.5" step="0.1"
          value={data.truss_depth || 0.6}
          onChange={(e) => onChange({ truss_depth: parseFloat(e.target.value) || 0.6 })}
          className="w-full h-1 bg-gray-200 rounded accent-blue-600" />
        <div className="mt-1 text-[9px] text-gray-400">
          Najwyższy pkt dachu (górna fałda blachy): <span className="text-blue-600 font-bold">
            {(parseFloat(data.clear_height || 0) + parseFloat(data.truss_depth || 0) + parseFloat(data.roof_sheet_height || 0.085)).toFixed(2)} m
          </span>
        </div>
      </div>
    </div>
  );
};

export default RoofSection;
