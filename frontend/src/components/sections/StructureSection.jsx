import React from 'react';

const COLUMN_CATEGORIES = [
  { key: 'external_main', label: 'Słupy główne zewnętrzne' },
  { key: 'external_corner', label: 'Słupy zewnętrzne narożne' },
  { key: 'external_intermediate_cladding', label: 'Słupy pośrednie pod obudowę' },
  { key: 'internal_main', label: 'Słupy wewnętrzne' },
];

const FOUNDATION_CATEGORIES = [
  { key: 'external_main', label: 'Stopy pod słupy główne zewn.' },
  { key: 'external_corner', label: 'Stopy pod słupy narożne' },
  { key: 'external_intermediate_cladding', label: 'Stopy pod słupy pośrednie' },
  { key: 'internal_main', label: 'Stopy pod słupy wewnętrzne' },
];

/**
 * StructureSection — columns (4 categories), foundations (4 categories), depths, plinth.
 * @param {object} data - fields: column_method, manual_column_sections, foundation_method, manual_sizes, foundation_depth, dock_foundation_depth, plinth_thickness, plinth_top_level
 * @param {function} onChange - (updates) => void  OR  (prevData => newData) for nested updates
 */
const StructureSection = ({ data, onChange }) => {
  const columnSections = data.manual_column_sections || {
    external_main: [0.4, 0.4], external_corner: [0.4, 0.4],
    external_intermediate_cladding: [0.3, 0.3], internal_main: [0.4, 0.4]
  };

  const manualSizes = data.manual_sizes || {
    external_main: [2.5, 4.0, 0.45], external_corner: [2.5, 4.0, 0.45],
    external_intermediate_cladding: [1.5, 1.5, 0.40], internal_main: [2.5, 2.5, 0.45]
  };

  return (
    <div className="flex flex-col gap-4">

      {/* --- SŁUPY --- */}
      <div>
        <span className="text-[10px] font-bold text-gray-500 uppercase mb-1 block">Metoda doboru słupów</span>
        <select value={data.column_method || 'default'}
          onChange={(e) => onChange({ column_method: e.target.value })}
          className="w-full p-2 border rounded text-[10px] font-bold bg-gray-50">
          <option value="default">Domyślne przekroje</option>
          <option value="manual">Ręczne przekroje [X, Z]</option>
        </select>

        {data.column_method === 'manual' && (
          <div className="mt-2 bg-gray-50 p-2 rounded flex flex-col gap-2 border border-gray-200">
            {COLUMN_CATEGORIES.map(cat => (
              <div key={cat.key} className="flex flex-col gap-1">
                <label className="text-[8px] font-bold text-gray-500 uppercase">{cat.label}</label>
                <div className="flex gap-1">
                  {(columnSections[cat.key] || [0.4, 0.4]).map((v, i) => (
                    <input key={i} type="number" step="0.05" value={v}
                      onChange={(e) => {
                        const newSections = { ...columnSections };
                        newSections[cat.key] = [...(newSections[cat.key] || [0.4, 0.4])];
                        newSections[cat.key][i] = parseFloat(e.target.value) || 0;
                        onChange({ manual_column_sections: newSections });
                      }}
                      className="w-full p-1 border text-[10px] text-center rounded font-mono" />
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
        <select value={data.foundation_method || 'default'}
          onChange={(e) => onChange({ foundation_method: e.target.value })}
          className="w-full p-2 border rounded text-[10px] font-bold bg-gray-50">
          <option value="default">Gabaryty domyślne</option>
          <option value="manual">Gabaryty ręczne [A, B, H]</option>
        </select>

        {data.foundation_method === 'manual' && (
          <div className="mt-2 bg-blue-50/50 p-2 rounded flex flex-col gap-2 border border-blue-100">
            {FOUNDATION_CATEGORIES.map(cat => (
              <div key={cat.key} className="flex flex-col gap-1">
                <label className="text-[8px] font-bold text-gray-500 uppercase">{cat.label}</label>
                <div className="flex gap-1">
                  {(manualSizes[cat.key] || [2.0, 2.0, 0.5]).map((v, i) => (
                    <input key={i} type="number" step="0.1" value={v}
                      onChange={(e) => {
                        const newSizes = { ...manualSizes };
                        newSizes[cat.key] = [...(newSizes[cat.key] || [2.0, 2.0, 0.5])];
                        newSizes[cat.key][i] = parseFloat(e.target.value) || 0;
                        onChange({ manual_sizes: newSizes });
                      }}
                      className="w-full p-1 border text-[10px] text-center rounded font-mono" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex flex-col gap-2 mt-4">
          <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
            <label>Zagłębienie główne [m]</label>
            <span className="text-blue-600">{data.foundation_depth || 1.0}</span>
          </div>
          <input type="range" min="0.5" max="2.0" step="0.1"
            value={data.foundation_depth || 1.0}
            onChange={(e) => onChange({ foundation_depth: parseFloat(e.target.value) })}
            className="w-full h-1 bg-gray-200 rounded accent-blue-600" />

          <div className="flex justify-between text-[10px] font-bold text-orange-600 uppercase mt-2">
            <label>Zagłębienie dokowe [m]</label>
            <span className="text-orange-600">{data.dock_foundation_depth || 1.2}</span>
          </div>
          <input type="range" min="0.8" max="2.5" step="0.1"
            value={data.dock_foundation_depth || 1.2}
            onChange={(e) => onChange({ dock_foundation_depth: parseFloat(e.target.value) })}
            className="w-full h-1 bg-orange-200 rounded accent-orange-600" />
        </div>
      </div>

      {/* --- COKÓŁ --- */}
      <div className="border-t border-gray-100 pt-3">
        <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
          <label>Poziom cokołu [m]</label>
          <span className="text-blue-600">{data.plinth_top_level || 0.30}</span>
        </div>
        <input type="range" min="0.15" max="0.60" step="0.05"
          value={data.plinth_top_level || 0.30}
          onChange={(e) => onChange({ plinth_top_level: parseFloat(e.target.value) })}
          className="w-full h-1 bg-gray-200 rounded accent-blue-600" />
      </div>
    </div>
  );
};

export default StructureSection;
