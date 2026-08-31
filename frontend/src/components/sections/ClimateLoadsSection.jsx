import React from 'react';

/**
 * ClimateLoadsSection — parametry lokalizacyjne do zebrania obciążeń dachu
 * (strefa śniegowa, wysokość n.p.m., ekspozycja, strefa wiatrowa, kategoria terenu).
 * Jedne na cały projekt — niezależne od liczby modułów (widoczne zarówno w Simple, jak i Complex).
 * @param {object} data - fields: snow_zone, terrain_altitude_m, snow_exposure, snow_thermal_coefficient, wind_zone, terrain_category, qdop_kpa, soil_type_id
 * @param {function} onChange - (updates) => void
 * @param {Array} soilCatalog - lista gruntów (z pliku Excel), pola: ID, Rodzaj gruntu, qdop [kPa], Ciężar objętościowy [kN/m3]
 */
const ClimateLoadsSection = ({ data, onChange, soilCatalog }) => {
  return (
    <div className="flex flex-col gap-3">
      <div className="text-[9px] text-gray-400 italic -mt-1">
        Parametry lokalizacji inwestycji — wspólne dla całej hali, użyte w zebraniu obciążeń dachu (zakładka „Obciążenia").
      </div>

      <div className="flex flex-col border-t pt-2">
        <span className="text-[10px] font-bold text-gray-500 uppercase mb-1">Śnieg</span>
        <div className="flex gap-2">
          <div className="flex-1">
            <span className="text-[8px] font-bold text-gray-500 uppercase">Strefa śniegowa</span>
            <select value={data.snow_zone || 2}
              onChange={(e) => onChange({ snow_zone: parseInt(e.target.value) })}
              className="w-full p-1.5 border rounded text-[10px] font-bold bg-gray-50">
              {[1, 2, 3, 4, 5].map(z => <option key={z} value={z}>Strefa {z}</option>)}
            </select>
          </div>
          <div className="flex-1">
            <span className="text-[8px] font-bold text-gray-500 uppercase">Wysokość [m n.p.m.]</span>
            <input type="number" min="0" step="10"
              value={data.terrain_altitude_m ?? 100}
              onChange={(e) => onChange({ terrain_altitude_m: parseFloat(e.target.value) || 0 })}
              className="w-full p-1.5 border rounded text-[10px] font-bold bg-gray-50" />
          </div>
        </div>
        <div className="flex gap-2 mt-1.5">
          <div className="flex-1">
            <span className="text-[8px] font-bold text-gray-500 uppercase">Ekspozycja na wiatr</span>
            <select value={data.snow_exposure || 'normalna'}
              onChange={(e) => onChange({ snow_exposure: e.target.value })}
              className="w-full p-1.5 border rounded text-[10px] font-bold bg-gray-50">
              <option value="wietrzna">Wietrzna (Ce=0,8)</option>
              <option value="normalna">Normalna (Ce=1,0)</option>
              <option value="oslonieta">Osłonięta (Ce=1,2)</option>
            </select>
          </div>
          <div className="flex-1">
            <span className="text-[8px] font-bold text-gray-500 uppercase">Wsp. termiczny Ct</span>
            <input type="number" min="0.5" max="1.2" step="0.1"
              value={data.snow_thermal_coefficient ?? 1.0}
              onChange={(e) => onChange({ snow_thermal_coefficient: parseFloat(e.target.value) || 1.0 })}
              className="w-full p-1.5 border rounded text-[10px] font-bold bg-gray-50" />
          </div>
        </div>
      </div>

      <div className="flex flex-col border-t pt-2">
        <span className="text-[10px] font-bold text-gray-500 uppercase mb-1">Wiatr</span>
        <div className="flex gap-2">
          <div className="flex-1">
            <span className="text-[8px] font-bold text-gray-500 uppercase">Strefa wiatrowa</span>
            <select value={data.wind_zone || 1}
              onChange={(e) => onChange({ wind_zone: parseInt(e.target.value) })}
              className="w-full p-1.5 border rounded text-[10px] font-bold bg-gray-50">
              {[1, 2, 3].map(z => <option key={z} value={z}>Strefa {z}</option>)}
            </select>
          </div>
          <div className="flex-1">
            <span className="text-[8px] font-bold text-gray-500 uppercase">Kategoria terenu</span>
            <select value={data.terrain_category || 'II'}
              onChange={(e) => onChange({ terrain_category: e.target.value })}
              className="w-full p-1.5 border rounded text-[10px] font-bold bg-gray-50">
              {['0', 'I', 'II', 'III', 'IV'].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="flex flex-col border-t pt-2">
        <span className="text-[10px] font-bold text-gray-500 uppercase mb-1">Grunt (do doboru gabarytów stóp fundamentowych)</span>
        <span className="text-[8px] font-bold text-gray-500 uppercase">Rodzaj gruntu (podpowiedź qdop)</span>
        <select value={data.soil_type_id || ''}
          onChange={(e) => {
            const id = e.target.value;
            const soil = (soilCatalog || []).find(s => s.ID === id);
            onChange(soil ? { soil_type_id: id, qdop_kpa: soil['qdop [kPa]'] } : { soil_type_id: id });
          }}
          className="w-full p-1.5 border rounded text-[10px] font-bold bg-gray-50">
          <option value="">— wybierz z katalogu (opcjonalnie) —</option>
          {(soilCatalog || []).map((s) => (
            <option key={s.ID} value={s.ID}>{s['Rodzaj gruntu']} (qdop≈{s['qdop [kPa]']} kPa)</option>
          ))}
        </select>
        <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase mt-1.5">
          <label>Dopuszczalne obciążenie gruntu qdop [kPa]</label>
          <input type="number" min="1" step="10"
            value={data.qdop_kpa ?? 150}
            onChange={(e) => onChange({ qdop_kpa: parseFloat(e.target.value) || 1 })}
            className="w-16 text-right text-blue-600 font-bold bg-transparent border-b border-blue-200 focus:outline-none text-[10px]" />
        </div>
        <div className="mt-1 text-[9px] text-gray-400">
          Katalog gruntów jest tylko podpowiedzią startową — wartość qdop powinna wynikać z dokumentacji geotechnicznej działki.
        </div>
      </div>

      <div className="mt-1 text-[9px] text-amber-600 bg-amber-50 border border-amber-200 rounded p-2">
        ⚠ Wartości strefowe i współczynniki użyte w zebraniu obciążeń są orientacyjne —
        wymagają weryfikacji z aktualnym załącznikiem krajowym normy przed wymiarowaniem konstrukcji.
      </div>
    </div>
  );
};

export default ClimateLoadsSection;
