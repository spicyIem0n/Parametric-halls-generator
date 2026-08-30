import React from 'react';

/**
 * QuantityTakeoffView — tabela przedmiaru ilościowego.
 * @param {Array} items - pozycje przedmiaru { lp, opis, jednostka, ilosc, cena_jedn, wartosc, uwagi }
 * @param {function} onExport - handler eksportu do Excel
 */
const QuantityTakeoffView = ({ items, onExport }) => {
  const hasData = items && items.length > 0;

  const fmt = (v) => {
    if (v === null || v === undefined) return '';
    if (typeof v === 'number') {
      return v.toLocaleString('pl-PL', { maximumFractionDigits: 3 });
    }
    return v;
  };

  return (
    <div className="flex-1 h-full w-full bg-gray-50 flex flex-col">
      {/* Pasek narzędzi */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shadow-sm">
        <h2 className="text-sm font-black text-gray-800 uppercase tracking-wider">
          Przedmiar ilościowy
        </h2>
        <button
          onClick={onExport}
          disabled={!hasData}
          className="px-3 py-1.5 text-[11px] font-bold rounded border border-green-300 bg-green-50 text-green-700 hover:bg-green-100 disabled:opacity-40 disabled:cursor-not-allowed uppercase tracking-wide"
        >
          Eksportuj do Excel
        </button>
      </div>

      {/* Tabela */}
      <div className="flex-1 overflow-auto p-4">
        {!hasData ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm italic">
            Brak danych. Kliknij „Buduj Model 3D", aby wygenerować przedmiar.
          </div>
        ) : (
          <table className="w-full border-collapse text-[11px] bg-white shadow-sm">
            <thead>
              <tr className="bg-blue-900 text-white">
                <th className="border border-blue-800 px-2 py-2 w-12 text-center">L.p.</th>
                <th className="border border-blue-800 px-2 py-2 text-left">Opis pozycji</th>
                <th className="border border-blue-800 px-2 py-2 w-20 text-center">Jednostka miary</th>
                <th className="border border-blue-800 px-2 py-2 w-24 text-center">Ilość</th>
                <th className="border border-blue-800 px-2 py-2 w-28 text-center">Cena jednostkowa</th>
                <th className="border border-blue-800 px-2 py-2 w-24 text-center">Wartość</th>
                <th className="border border-blue-800 px-2 py-2 w-40 text-left">Uwagi</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.lp} className="odd:bg-white even:bg-gray-50 hover:bg-blue-50">
                  <td className="border border-gray-200 px-2 py-1 text-center">{it.lp}</td>
                  <td className="border border-gray-200 px-2 py-1 text-left">{it.opis}</td>
                  <td className="border border-gray-200 px-2 py-1 text-center">{it.jednostka}</td>
                  <td className="border border-gray-200 px-2 py-1 text-right font-mono">{fmt(it.ilosc)}</td>
                  <td className="border border-gray-200 px-2 py-1 text-right text-gray-300">{fmt(it.cena_jedn)}</td>
                  <td className="border border-gray-200 px-2 py-1 text-right text-gray-300">{fmt(it.wartosc)}</td>
                  <td className="border border-gray-200 px-2 py-1 text-left text-gray-500">{it.uwagi}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default QuantityTakeoffView;
