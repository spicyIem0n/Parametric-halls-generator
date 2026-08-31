import React from 'react';

const CATEGORY_ORDER = ['stałe', 'śnieg', 'wiatr', 'użytkowe'];
const CATEGORY_LABELS = {
  'stałe': 'Obciążenia stałe (G)',
  'śnieg': 'Śnieg (Q — zmienne)',
  'wiatr': 'Wiatr (Q — zmienne, uproszczony)',
  'użytkowe': 'Obciążenie użytkowe (Q — zmienne)',
};
const CATEGORY_COLORS = {
  'stałe': 'bg-slate-700',
  'śnieg': 'bg-sky-700',
  'wiatr': 'bg-teal-700',
  'użytkowe': 'bg-amber-700',
};

/**
 * RoofLoadsView — zebranie obciążeń dachu (wartości charakterystyczne), per moduł.
 * @param {object} data - wynik z /roof-loads: { blocks: [{ block_id, items, summary }], assumptions }
 */
const RoofLoadsView = ({ data }) => {
  const blocks = data && data.blocks ? data.blocks : [];
  const hasData = blocks.length > 0;

  const fmt = (v) => {
    if (v === null || v === undefined) return '';
    if (typeof v === 'number') return v.toLocaleString('pl-PL', { maximumFractionDigits: 3 });
    return v;
  };

  const grouped = (items) => {
    const g = {};
    for (const it of items) {
      if (!g[it.kategoria]) g[it.kategoria] = [];
      g[it.kategoria].push(it);
    }
    return g;
  };

  return (
    <div className="flex-1 h-full w-full bg-gray-50 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shadow-sm">
        <h2 className="text-sm font-black text-gray-800 uppercase tracking-wider">
          Zebranie obciążeń dachu
        </h2>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {!hasData ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm italic">
            Brak danych. Kliknij „Buduj Model 3D", aby wyliczyć obciążenia.
          </div>
        ) : (
          <div className="flex flex-col gap-5 max-w-5xl mx-auto">
            {data.assumptions && (
              <div className="text-[11px] text-amber-800 bg-amber-50 border border-amber-300 rounded p-3 leading-relaxed">
                ⚠ {data.assumptions}
              </div>
            )}

            {blocks.map((blk) => {
              const byCategory = grouped(blk.items);
              return (
                <div key={blk.block_id} className="bg-white rounded shadow-sm border border-gray-200 overflow-hidden">
                  <div className="bg-blue-900 text-white px-3 py-2 flex items-center justify-between">
                    <span className="text-xs font-black uppercase tracking-wide">Moduł: {blk.block_id}</span>
                    <span className="text-[10px] text-blue-200">
                      wysokość odniesienia h={fmt(blk.summary?.wysokosc_odniesienia_m)} m
                    </span>
                  </div>

                  {/* Podsumowanie */}
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-px bg-gray-200 text-center">
                    {[
                      ['Σ Stałe', blk.summary?.stale_kn_m2],
                      ['Śnieg (równ.)', blk.summary?.sniegu_rownomiernego_kn_m2],
                      ['Wiatr (krawędź)', blk.summary?.wiatr_krawedziowy_kn_m2],
                      ['Wiatr (środek)', blk.summary?.wiatr_srodkowy_kn_m2],
                      ['Użytkowe', blk.summary?.uzytkowe_kn_m2],
                    ].map(([label, val]) => (
                      <div key={label} className="bg-white py-2 px-1">
                        <div className="text-[8px] font-bold text-gray-400 uppercase">{label}</div>
                        <div className="text-sm font-black text-gray-800">{fmt(val)} <span className="text-[9px] font-normal text-gray-400">kN/m²</span></div>
                      </div>
                    ))}
                  </div>

                  {/* Tabele per kategoria */}
                  <table className="w-full border-collapse text-[11px]">
                    <tbody>
                      {CATEGORY_ORDER.filter(cat => byCategory[cat]).map((cat) => (
                        <React.Fragment key={cat}>
                          <tr>
                            <td colSpan={4} className={`${CATEGORY_COLORS[cat]} text-white text-[10px] font-bold uppercase px-2 py-1`}>
                              {CATEGORY_LABELS[cat]}
                            </td>
                          </tr>
                          {byCategory[cat].map((it, idx) => (
                            <tr key={idx} className="odd:bg-white even:bg-gray-50 hover:bg-blue-50">
                              <td className="border border-gray-200 px-2 py-1 text-left w-1/2">{it.opis}</td>
                              <td className="border border-gray-200 px-2 py-1 text-right font-mono w-24">{fmt(it.wartosc)}</td>
                              <td className="border border-gray-200 px-2 py-1 text-center w-16 text-gray-500">{it.jednostka}</td>
                              <td className="border border-gray-200 px-2 py-1 text-left text-gray-400">{it.uwagi}</td>
                            </tr>
                          ))}
                        </React.Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default RoofLoadsView;
