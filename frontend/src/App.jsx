import React, { useState, useEffect } from 'react';
import Controls from './components/Controls';
import Scene3D from './components/Scene3D';
import { generateHallParameters, validateHall } from './api';

// Baza danych płyt warstwowych oparta na oficjalnym katalogu Ruukki
export const RUUKKI_CATALOG = {
  "SP2B_E_PIR_100": { name: "SP2B E-PIR", core: "PIR", thickness: 100, uValue: 0.22, fire: "EI 15", modularWidth: 1100, img: "standard_pir" },
  "SP2B_E_PIR_150": { name: "SP2B E-PIR", core: "PIR", thickness: 150, uValue: 0.14, fire: "EI 20", modularWidth: 1100, img: "standard_pir" },
  "SP2E_X_PIR_120": { name: "SP2E X-PIR Energy", core: "PIR", thickness: 120, uValue: 0.18, fire: "EI 30", modularWidth: 1100, img: "energy_pir" },
  "SP2E_X_PIR_160": { name: "SP2E X-PIR Energy", core: "PIR", thickness: 160, uValue: 0.14, fire: "EI 60", modularWidth: 1100, img: "energy_pir" },
  "nSPB_WE_100": { name: "nSPB WE", core: "Wełna Mineralna", thickness: 100, uValue: 0.39, fire: "EI 60", modularWidth: 1100, img: "standard_wool" },
  "nSPB_WE_150": { name: "nSPB WE", core: "Wełna Mineralna", thickness: 150, uValue: 0.26, fire: "EI 120", modularWidth: 1100, img: "standard_wool" }
};

// Katalog blach trapezowych dachowych (na podstawie oferty Pruszyński)
export const ROOF_SHEET_CATALOG = {
  "T55_07": { name: "T55", thickness: 0.7, height: 55, span: 3.0, weight: 7.6, desc: "Blacha nośna lekka" },
  "T85_08": { name: "T85", thickness: 0.8, height: 85, span: 5.0, weight: 9.2, desc: "Blacha nośna średnia" },
  "T100_088": { name: "T100", thickness: 0.88, height: 100, span: 6.0, weight: 10.8, desc: "Blacha nośna ciężka" },
  "T130_10": { name: "T130", thickness: 1.0, height: 130, span: 7.5, weight: 13.4, desc: "Blacha nośna wzmocniona" },
  "T150_10": { name: "T150", thickness: 1.0, height: 150, span: 9.0, weight: 14.8, desc: "Blacha nośna max rozpiętość" },
  "T160_125": { name: "T160", thickness: 1.25, height: 160, span: 10.0, weight: 17.2, desc: "Blacha nośna przemysłowa" },
};

const App = () => {
  //... (Górna część i baza Ruukki pozostają bez zmian) ...
  const [params, setParams] = useState({
    hall_type: 'simple', length: 60, width: 30, clear_height: 8, number_of_aisles: 1, roof_angle: 5, bay_spacing: 6,
    floor_thickness: 0.2, floor_base_type: 'lean_concrete', floor_base_thickness: 0.15,
   foundation_method: 'default', foundation_depth: 1.0, 
    docks_config: {}, dock_foundation_depth: 1.2,
    dock_zone_enabled: false, dock_zone_side: "left", dock_zone_width: 12, dock_zone_aisles: 1,
    manual_sizes: { external_main: [2.5, 4.0, 0.45], external_corner: [2.5, 4.0, 0.45], external_intermediate_cladding: [1.5, 1.5, 0.40], internal_main: [2.5, 2.5, 0.45] },
    column_method: 'default',
    manual_column_sections: { external_main: [0.4, 0.4], external_corner: [0.4, 0.4], external_intermediate_cladding: [0.3, 0.3], internal_main: [0.4, 0.4] },
    has_cladding: true, cladding_orientation: 'horizontal', cladding_panel_id: 'SP2B_E_PIR_100', cladding_thickness: 0.1, cladding_bottom_level: 0.25,
    plinth_thickness: 0.24, plinth_top_level: 0.30, purlin_spacing: 2.0, roof_panel_thickness: 0.15, truss_depth: 0.8,
    roof_sheet_id: "T85_08", roof_sheet_height: 0.085,
    // NOWE: Parametry odwodnienia
    roof_drainage_type: 'vacuum', drainage_zones_x: 2, drainage_zones_z: 3, roof_slope_percent: 2.0,
    // NOWE: Wielobryłowość
    blocks: [],
    // NOWE: PPOŻ
    fire_load_qd: 500, has_sprinklers: false, fire_walls: [],
    // NOWE: Stężenia
    bracing_config: { wall_bracing_bays: [], roof_bracing: true, bracing_type: 'x_cross' },
    // NOWE: Pomieszczenia i biura
    technical_rooms: [], external_offices: [], internal_offices: [], office_reserve_zones: [],
    roof_lights: [],
    module_connections: [],
  });
//... (Reszta App.jsx bez zmian) ...

  const [components, setComponents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [validation, setValidation] = useState(null);

  // Funkcja aktualizująca grubość panelu do API po wybraniu go z katalogu
  const handlePanelChange = (panelId) => {
    const selectedPanel = RUUKKI_CATALOG[panelId];
    setParams(prev => ({ ...prev, cladding_panel_id: panelId, cladding_thickness: selectedPanel.thickness / 1000 }));
  };

  const handleGenerate = async () => {
    setIsLoading(true);
    // Strip internal UI-only fields (prefixed with _) before sending to API
    const apiParams = Object.fromEntries(
      Object.entries(params).filter(([key]) => !key.startsWith('_'))
    );
    const data = await generateHallParameters(apiParams);
    if (data && data.components) setComponents(data.components);
    // Walidacja modelu
    const validationResult = await validateHall(apiParams);
    setValidation(validationResult);
    setIsLoading(false);
  };

  useEffect(() => { handleGenerate(); }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-100 font-sans">
      <Controls params={params} setParams={setParams} onGenerate={handleGenerate} isLoading={isLoading} onPanelChange={handlePanelChange} catalog={RUUKKI_CATALOG} roofSheetCatalog={ROOF_SHEET_CATALOG} validation={validation} />
      <Scene3D components={components} />
    </div>
  );
};

export default App;
