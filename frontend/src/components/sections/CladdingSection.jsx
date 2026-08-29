import React from 'react';

/**
 * CladdingSection — panel obudowy, orientacja płyt.
 * @param {object} data - fields: has_cladding, cladding_panel_id, cladding_orientation
 * @param {function} onChange - (updates) => void
 * @param {object} catalog - RUUKKI_CATALOG
 */
const CladdingSection = ({ data, onChange, catalog }) => {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold uppercase text-gray-500">Płyty ścienne</span>
        <input type="checkbox" checked={data.has_cladding !== false}
          onChange={(e) => onChange({ has_cladding: e.target.checked })}
          className="rounded" />
      </div>

      {data.has_cladding !== false && catalog && (
        <select value={data.cladding_panel_id || 'SP2B_E_PIR_100'}
          onChange={(e) => {
            const panel = catalog[e.target.value];
            onChange({
              cladding_panel_id: e.target.value,
              cladding_thickness: panel ? panel.thickness / 1000 : 0.1
            });
          }}
          className="w-full p-2 border rounded text-[10px] font-bold text-blue-900 bg-blue-50">
          {Object.entries(catalog).map(([id, panel]) => (
            <option key={id} value={id}>{panel.name} ({panel.thickness}mm)</option>
          ))}
        </select>
      )}

      {data.has_cladding !== false && (
        <div className="mt-2">
          <span className="text-[10px] font-bold uppercase text-gray-500 block mb-1">Układ płyt</span>
          <select value={data.cladding_orientation || 'horizontal'}
            onChange={(e) => onChange({ cladding_orientation: e.target.value })}
            className="w-full p-2 border rounded text-[10px] font-bold bg-gray-50">
            <option value="horizontal">Poziomy (standardowy)</option>
            <option value="vertical">Pionowy (z ryglami montażowymi)</option>
          </select>
        </div>
      )}
    </div>
  );
};

export default CladdingSection;
