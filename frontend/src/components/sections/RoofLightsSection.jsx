import React from 'react';

/**
 * RoofLightsSection — per-zone roof lights/smoke vents with area calculations.
 * @param {object} data - fields: roof_lights, dock_zone_enabled, dock_zone_side, dock_zone_width, width, length
 * @param {function} onChange - (updates) => void
 */
const RoofLightsSection = ({ data, onChange }) => {
  const roofLights = data.roof_lights || [];
  const zones = ["main", ...(data.dock_zone_enabled ? ["dock_zone"] : [])];

  const updateZones = (newZones) => onChange({ roof_lights: newZones });

  const computeZoneWidth = (zoneId) => {
    if (zoneId === "dock_zone") {
      return (data.dock_zone_width || 12) * (data.dock_zone_side === "both" ? 2 : 1);
    }
    const dockW = data.dock_zone_enabled
      ? (data.dock_zone_width || 12) * (data.dock_zone_side === "both" ? 2 : 1)
      : 0;
    return (data.width || 30) - dockW;
  };

  const computeAreas = (items) => {
    let skylightArea = 0, ventArea = 0;
    (items || []).forEach(item => {
      const a = item.width * item.length * item.quantity;
      if (item.item_type === "skylight" || item.item_type === "light_strip") skylightArea += a;
      if (item.item_type === "smoke_vent") ventArea += a;
      if (item.item_type === "light_strip_with_vents") {
        const ventsInStrip = item.width * (item.vent_length || 2) * (item.vent_count || 0) * item.quantity;
        skylightArea += a - ventsInStrip;
        ventArea += ventsInStrip;
      }
    });
    return { skylightArea, ventArea };
  };

  return (
    <div className="flex flex-col gap-3">
      {zones.map(zoneId => {
        const zoneConfig = roofLights.find(z => z.zone_id === zoneId) || { zone_id: zoneId, items: [] };
        const zoneItems = zoneConfig.items || [];
        const zoneName = zoneId === "main" ? "Strefa magazynowa" : "Strefa dokowa";
        const zoneWidth = computeZoneWidth(zoneId);
        const zoneArea = zoneWidth * (data.length || 60);
        const { skylightArea, ventArea } = computeAreas(zoneItems);

        return (
          <div key={zoneId} className="border border-gray-200 rounded p-2 mb-2">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-black text-cyan-800 uppercase">{zoneName}</span>
              <button onClick={() => {
                const newItem = { item_id: `${zoneId}_${Date.now()}`, item_type: "skylight", width: 2.0, length: 3.0, quantity: 4, vent_count: 2, vent_length: 2.0 };
                const newZones = [...roofLights];
                const idx = newZones.findIndex(z => z.zone_id === zoneId);
                if (idx >= 0) { newZones[idx] = { ...newZones[idx], items: [...newZones[idx].items, newItem] }; }
                else { newZones.push({ zone_id: zoneId, items: [newItem] }); }
                updateZones(newZones);
              }} className="text-[8px] bg-cyan-50 text-cyan-700 px-2 py-1 rounded">+ Pozycja</button>
            </div>

            {zoneItems.map((item, itemIdx) => (
              <div key={item.item_id} className="bg-gray-50 p-1.5 rounded border border-gray-100 mb-1">
                <div className="flex gap-1 items-center mb-1">
                  <select value={item.item_type} onChange={(e) => {
                    const newType = e.target.value;
                    const isStrip = newType === "light_strip" || newType === "light_strip_with_vents";
                    const fullStripLen = Math.max(6, Math.round(((data.length || 60) - 2) * 2) / 2);
                    const newZones = [...roofLights];
                    const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                    if (zIdx >= 0) {
                      const newItems = [...newZones[zIdx].items];
                      const cur = newItems[itemIdx];
                      let len = cur.length;
                      if (isStrip && len < (data.length || 60) * 0.5) len = fullStripLen;
                      if (!isStrip && len > 10) len = 3.0;
                      newItems[itemIdx] = { ...cur, item_type: newType, length: len };
                      newZones[zIdx] = { ...newZones[zIdx], items: newItems };
                    }
                    updateZones(newZones);
                  }} className="flex-1 p-1 border text-[8px] rounded">
                    <option value="skylight">Świetlik</option>
                    <option value="smoke_vent">Klapa dymowa</option>
                    <option value="light_strip">Pasmo świetlne</option>
                    <option value="light_strip_with_vents">Pasmo z klapami</option>
                  </select>
                  <button onClick={() => {
                    const newZones = [...roofLights];
                    const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                    if (zIdx >= 0) {
                      const newItems = [...newZones[zIdx].items];
                      newItems.splice(itemIdx, 1);
                      newZones[zIdx] = { ...newZones[zIdx], items: newItems };
                    }
                    updateZones(newZones);
                  }} className="text-[8px] text-red-500 px-1">X</button>
                </div>

                <div className="grid grid-cols-3 gap-1">
                  <div className="flex flex-col"><span className="text-[7px] text-gray-400">Szer[m]</span>
                    <input type="number" step="0.5" min="0.5" max="6" value={item.width} onChange={(e) => {
                      const newZones = [...roofLights];
                      const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                      if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], width: parseFloat(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                      updateZones(newZones);
                    }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                  <div className="flex flex-col"><span className="text-[7px] text-gray-400">Dł[m]</span>
                    <input type="number" step="0.5" min="1" max="400" value={item.length} onChange={(e) => {
                      const newZones = [...roofLights];
                      const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                      if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], length: parseFloat(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                      updateZones(newZones);
                    }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                  <div className="flex flex-col"><span className="text-[7px] text-gray-400">Ilość</span>
                    <input type="number" step="1" min="1" max="50" value={item.quantity} onChange={(e) => {
                      const newZones = [...roofLights];
                      const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                      if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], quantity: parseInt(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                      updateZones(newZones);
                    }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                </div>

                {item.item_type === "light_strip_with_vents" && (
                  <div className="grid grid-cols-2 gap-1 mt-1 border-t pt-1">
                    <div className="flex flex-col"><span className="text-[7px] text-gray-400">Klap [szt]</span>
                      <input type="number" step="1" min="1" max="20" value={item.vent_count} onChange={(e) => {
                        const newZones = [...roofLights];
                        const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                        if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], vent_count: parseInt(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                        updateZones(newZones);
                      }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                    <div className="flex flex-col"><span className="text-[7px] text-gray-400">Dł klapy[m]</span>
                      <input type="number" step="0.5" min="1" max="6" value={item.vent_length} onChange={(e) => {
                        const newZones = [...roofLights];
                        const zIdx = newZones.findIndex(z => z.zone_id === zoneId);
                        if (zIdx >= 0) { const ni = [...newZones[zIdx].items]; ni[itemIdx] = {...ni[itemIdx], vent_length: parseFloat(e.target.value)||1}; newZones[zIdx]={...newZones[zIdx],items:ni}; }
                        updateZones(newZones);
                      }} className="p-0.5 border text-[9px] text-center rounded" /></div>
                  </div>
                )}
              </div>
            ))}

            <div className="bg-cyan-50/50 rounded p-1.5 mt-1 text-[8px] text-gray-600">
              <div>Pow. świetlików: <b>{skylightArea.toFixed(1)} m²</b></div>
              <div>Pow. klap dymowych: <b>{ventArea.toFixed(1)} m²</b></div>
              <div>Łącznie: <b>{(skylightArea + ventArea).toFixed(1)} m²</b></div>
              <div>Udział w strefie ({zoneArea.toFixed(0)} m²): <b className="text-cyan-700">{zoneArea > 0 ? ((skylightArea + ventArea) / zoneArea * 100).toFixed(2) : 0}%</b></div>
            </div>
          </div>
        );
      })}

      {/* Global summary */}
      <div className="bg-gray-100 rounded p-1.5 text-[8px] text-gray-700 font-bold">
        Uśredniony wsp. doświetlenia+oddymiania / pow. budynku: <span className="text-cyan-700">
          {(() => {
            let totalLight = 0, totalVent = 0;
            roofLights.forEach(z => (z.items || []).forEach(item => {
              const a = item.width * item.length * item.quantity;
              if (item.item_type === "skylight" || item.item_type === "light_strip") totalLight += a;
              if (item.item_type === "smoke_vent") totalVent += a;
              if (item.item_type === "light_strip_with_vents") {
                const vInS = item.width * (item.vent_length||2) * (item.vent_count||0) * item.quantity;
                totalLight += a - vInS;
                totalVent += vInS;
              }
            }));
            const buildingArea = (data.width || 30) * (data.length || 60);
            return buildingArea > 0 ? ((totalLight + totalVent) / buildingArea * 100).toFixed(2) + "%" : "0%";
          })()}
        </span>
      </div>
    </div>
  );
};

export default RoofLightsSection;
