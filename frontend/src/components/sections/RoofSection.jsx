import React from 'react';

/**
 * RoofSection — typ odwodnienia, kąt dachu, płatwie, blacha, dźwigar, izolacje.
 * @param {object} data - fields: roof_drainage_type, roof_angle, purlin_spacing, roof_sheet_id, roof_sheet_height, truss_depth, clear_height,
 *   roof_thermal_insulation_enabled, roof_thermal_insulation_id, roof_waterproofing_enabled, roof_waterproofing_id,
 *   roof_suspended_load, roof_use_category
 * @param {function} onChange - (updates) => void
 * @param {object} roofSheetCatalog - catalog of roof sheets
 * @param {Array} thermalInsulationCatalog - lista wariantów izolacji termicznej dachu (z pliku Excel), pola: ID, Materiał, Grubość [cm], Lambda [W/mK], Ciężar właściwy [kg/m3]
 * @param {Array} waterproofingCatalog - lista wariantów izolacji przeciwwodnej dachu (z pliku Excel), pola: ID, Materiał, Grubość [mm], Ciężar właściwy [kg/m3]
 */
const RoofSection = ({ data, onChange, roofSheetCatalog, thermalInsulationCatalog, waterproofingCatalog }) => {
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

      {/* Izolacja termiczna dachu — lista wariantów wczytywana z pliku Excel (data/roof_insulation_catalog.xlsx) */}
      <div className="flex flex-col border-t pt-2 mt-2">
        <label className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase mb-1">
          <input type="checkbox"
            checked={!!data.roof_thermal_insulation_enabled}
            onChange={(e) => onChange({ roof_thermal_insulation_enabled: e.target.checked })} />
          Izolacja termiczna dachu
        </label>
        {data.roof_thermal_insulation_enabled && (
          <>
            <select value={data.roof_thermal_insulation_id || ""}
              onChange={(e) => onChange({ roof_thermal_insulation_id: e.target.value })}
              className="w-full p-2 border rounded bg-gray-50 text-[10px] font-bold">
              <option value="">— wybierz materiał —</option>
              {(thermalInsulationCatalog || []).map((item) => (
                <option key={item.ID} value={item.ID}>
                  {item["Materiał"]} — {item["Grubość [cm]"]} cm (λ={item["Lambda [W/mK]"]} W/mK, {item["Ciężar właściwy [kg/m3]"]} kg/m³)
                </option>
              ))}
            </select>
            {(!thermalInsulationCatalog || thermalInsulationCatalog.length === 0) && (
              <span className="mt-1 text-[9px] text-gray-400">Brak danych z katalogu (backend niedostępny lub pusty plik Excel).</span>
            )}
          </>
        )}
      </div>

      {/* Izolacja przeciwwodna dachu — lista wariantów wczytywana z pliku Excel (data/roof_insulation_catalog.xlsx) */}
      <div className="flex flex-col border-t pt-2 mt-2">
        <label className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase mb-1">
          <input type="checkbox"
            checked={!!data.roof_waterproofing_enabled}
            onChange={(e) => onChange({ roof_waterproofing_enabled: e.target.checked })} />
          Izolacja przeciwwodna dachu
        </label>
        {data.roof_waterproofing_enabled && (
          <>
            <select value={data.roof_waterproofing_id || ""}
              onChange={(e) => onChange({ roof_waterproofing_id: e.target.value })}
              className="w-full p-2 border rounded bg-gray-50 text-[10px] font-bold">
              <option value="">— wybierz materiał —</option>
              {(waterproofingCatalog || []).map((item) => (
                <option key={item.ID} value={item.ID}>
                  {item["Materiał"]} — {item["Grubość [mm]"]} mm ({item["Ciężar właściwy [kg/m3]"]} kg/m³)
                </option>
              ))}
            </select>
            {(!waterproofingCatalog || waterproofingCatalog.length === 0) && (
              <span className="mt-1 text-[9px] text-gray-400">Brak danych z katalogu (backend niedostępny lub pusty plik Excel).</span>
            )}
          </>
        )}
      </div>

      {/* Dane do zebrania obciążeń dachu (zakładka „Obciążenia") */}
      <div className="flex flex-col border-t pt-2 mt-2">
        <span className="text-[10px] font-bold text-gray-500 uppercase mb-1">Zebranie obciążeń — dane dodatkowe</span>
        <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase">
          <label>Sufit podwieszony / instalacje [kN/m²]</label>
          <input type="number" min="0" max="2" step="0.05"
            value={data.roof_suspended_load ?? 0.15}
            onChange={(e) => onChange({ roof_suspended_load: parseFloat(e.target.value) || 0 })}
            className="w-14 text-right text-blue-600 font-bold bg-transparent border-b border-blue-200 focus:outline-none text-[10px]" />
        </div>
        <div className="mt-1 text-[9px] text-gray-400">
          Kategoria użytkowa dachu: <span className="text-blue-600 font-bold">{data.roof_use_category || 'H'}</span> (dach niedostępny poza konserwacją, Q<sub>k</sub>=0,4 kN/m²)
        </div>
      </div>
    </div>
  );
};

export default RoofSection;
