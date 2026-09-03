import React, { useEffect, useState } from 'react';
import { verifyAdminToken, setFeatureFlag } from '../api';

const TOKEN_STORAGE_KEY = 'hale_admin_token';

/**
 * AdminPanel — ukryty panel administratora: uwierzytelnienie prostym tokenem
 * (ADMIN_TOKEN po stronie backendu) i przełączanie flag funkcji programu
 * (np. wyłączenie edycji cennika w wersji trialowej).
 *
 * @param {Object} flags - aktualny stan flag { nazwa: bool }
 * @param {function} onFlagsChanged - wywoływane z nowym stanem flag po udanej zmianie
 * @param {function} onClose - zamyka panel
 */
const AdminPanel = ({ flags, onFlagsChanged, onClose }) => {
  const [token, setToken] = useState('');
  const [authed, setAuthed] = useState(false);
  const [labels, setLabels] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  // Przy otwarciu panelu — spróbuj auto-zalogować zapamiętanym tokenem
  useEffect(() => {
    const saved = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (saved) {
      setToken(saved);
      handleLogin(saved);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogin = async (t) => {
    setBusy(true);
    setError('');
    const result = await verifyAdminToken(t);
    setBusy(false);
    if (result.ok) {
      setAuthed(true);
      setLabels(result.labels || {});
      localStorage.setItem(TOKEN_STORAGE_KEY, t);
    } else {
      setAuthed(false);
      setError(result.error || 'Nieprawidłowy token.');
    }
  };

  const handleToggle = async (name, current) => {
    setBusy(true);
    setError('');
    const result = await setFeatureFlag(token, name, !current);
    setBusy(false);
    if (result.ok) {
      onFlagsChanged(result.flags);
    } else {
      setError(result.error || 'Nie udało się zapisać.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setAuthed(false);
    setToken('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-[420px] max-w-[90vw] p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-black text-gray-800 uppercase tracking-wide">Panel administratora</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-lg leading-none">×</button>
        </div>

        {!authed ? (
          <div className="space-y-3">
            <label className="block text-[11px] font-bold text-gray-600 uppercase tracking-wide">
              Token administratora
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin(token)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              placeholder="ADMIN_TOKEN"
              autoFocus
            />
            {error && <div className="text-[11px] text-red-600">{error}</div>}
            <button
              onClick={() => handleLogin(token)}
              disabled={busy || !token}
              className="w-full px-3 py-2 text-[11px] font-bold rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 uppercase tracking-wide"
            >
              Zaloguj
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {Object.keys(flags).length === 0 && (
              <div className="text-[11px] text-gray-400 italic">Brak zdefiniowanych flag.</div>
            )}
            {Object.entries(flags).map(([name, value]) => (
              <label key={name} className="flex items-center justify-between gap-3 py-1.5 border-b border-gray-100">
                <span className="text-[12px] text-gray-700">{labels[name] || name}</span>
                <input
                  type="checkbox"
                  checked={!!value}
                  disabled={busy}
                  onChange={() => handleToggle(name, value)}
                  className="w-4 h-4"
                />
              </label>
            ))}
            {error && <div className="text-[11px] text-red-600">{error}</div>}
            <button
              onClick={handleLogout}
              className="text-[11px] text-gray-400 hover:text-gray-600 underline"
            >
              Wyloguj
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;
