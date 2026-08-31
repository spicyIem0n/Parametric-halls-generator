import React from 'react';

/**
 * FoundationSizingView — automatyczny dobór gabarytów stóp fundamentowych, per moduł.
 * @param {object} data - wynik z /foundation-sizing: { blocks: [{ block_id, categories }], qdop_kpa, assumptions }
 * @param {function} onApply - (block_id, categories) => void — wpisuje wynik do manual_sizes danego modułu/hali
 */
const FoundationSizingView = ({ data, onApply }) => {
  const blocks = data && data.blocks ? data.blocks : [];
  const hasData = blocks.length > 0;

  const fmt = (v) => {
    if (v === null || v === undefined) return '';
    if (typeof v === 'number') return v.toLocaleString('pl-PL', { maximumFractionDigits: 2 });
    return v;
  };

  return (
    <div className="flex-1 h-full w-full bg-gray-50 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shadow-sm">
        <h2 className="text-sm font-black text-gray-800 uppercase tracking-wider">
          Dobór gabarytów stóp fundamentowych
        </h2>
        {data.qdop_kpa != null && (
          <span className="text-[11px] text-gray-500 font-bold">qdop = {fmt(data.qdop_kpa)} kPa</span>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {!hasData ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm italic">
            Brak danych. Kliknij „Buduj Model 3D", aby wyliczyć gabaryty stóp.
          </div>
        ) : (
          <div className="flex flex-col gap-5 max-w-5xl mx-auto">
            {data.assumptions && (
              <div className="text-[11px] text-amber-800 bg-amber-50 border border-amber-300 rounded p-3 leading-relaxed">
                ⚠ {data.assumptions}
              </div>
            )}

            {blocks.map((blk) => (
              <div key={blk.block_id} className="bg-white rounded shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-blue-900 text-white px-3 py-2 flex items-center justify-between">
                  <span className="text-xs font-black uppercase tracking-wide">Moduł: {blk.block_id}</span>
                  {onApply && (
                    <button
                      onClick={() => onApply(blk.block_id, blk.categories)}
                      className="px-2.5 py-1 text-[10px] font-bold rounded border border-green-300 bg-green-50 text-green-700 hover:bg-green-100 uppercase tracking-wide"
                    >
                      Zastosuj do modelu
                    </button>
                  )}
                </div>

                <table className="w-full border-collapse text-[11px]">
                  <thead>
                    <tr className="bg-gray-100 text-gray-600">
                      <th className="border border-gray-200 px-2 py-1.5 text-left">Kategoria słupa</th>
                      <th className="border border-gray-200 px-2 py-1.5 text-right w-20">N [kN]</th>
                      <th className="border border-gray-200 px-2 py-1.5 text-right w-20">H [kN]</th>
                      <th className="border border-gray-200 px-2 py-1.5 text-right w-24">M [kNm]</th>
                      <th className="border border-gray-200 px-2 py-1.5 text-right w-36">Gabaryt a×b×h [m]</th>
                      <th className="border border-gray-200 px-2 py-1.5 text-left">Uwagi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {blk.categories.map((cat) => (
                      <tr key={cat.category} className="odd:bg-white even:bg-gray-50 hover:bg-blue-50">
                        <td className="border border-gray-200 px-2 py-1.5 text-left font-bold text-gray-700">{cat.label}</td>
                        <td className="border border-gray-200 px-2 py-1.5 text-right font-mono">{fmt(cat.n_kn)}</td>
                        <td className="border border-gray-200 px-2 py-1.5 text-right font-mono">{fmt(cat.h_kn)}</td>
                        <td className="border border-gray-200 px-2 py-1.5 text-right font-mono">{fmt(cat.m_knm)}</td>
                        <td className="border border-gray-200 px-2 py-1.5 text-right font-mono font-bold text-blue-700">
                          {fmt(cat.size?.a_m)} × {fmt(cat.size?.b_m)} × {fmt(cat.size?.h_m)}
                        </td>
                        <td className="border border-gray-200 px-2 py-1.5 text-left text-amber-700">
                          {(cat.warnings || []).map((w, i) => <div key={i}>⚠ {w}</div>)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FoundationSizingView;
