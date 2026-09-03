const API_URL = 'http://localhost:8000';

export const generateHallParameters = async (params) => {
    try {
        const response = await fetch(`${API_URL}/generate-hall`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        });
        
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error("Błąd podczas komunikacji z API:", error);
        return { components: [] };
    }
};

export const validateHall = async (params) => {
    try {
        const response = await fetch(`${API_URL}/validate-hall`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Błąd walidacji:", error);
        return { is_valid: true, clashes: [], warnings_count: 0, errors_count: 0 };
    }
};

export const getQuantityTakeoff = async (params) => {
    try {
        const response = await fetch(`${API_URL}/quantity-takeoff`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Błąd pobierania przedmiaru:", error);
        return { items: [] };
    }
};

export const getRoofLoads = async (params) => {
    try {
        const response = await fetch(`${API_URL}/roof-loads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Błąd pobierania zebrania obciążeń dachu:", error);
        return { blocks: [], assumptions: "" };
    }
};

export const getFoundationSizing = async (params) => {
    try {
        const response = await fetch(`${API_URL}/foundation-sizing`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Błąd pobierania doboru gabarytów stóp fundamentowych:", error);
        return { blocks: [], qdop_kpa: null, assumptions: "" };
    }
};

export const getSoilCatalog = async () => {
    try {
        const response = await fetch(`${API_URL}/catalogs/soil`);
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        const data = await response.json();
        return data && data.items ? data.items : [];
    } catch (error) {
        console.error("Błąd pobierania katalogu gruntów:", error);
        return [];
    }
};

export const getRoofThermalInsulationCatalog = async () => {
    try {
        const response = await fetch(`${API_URL}/catalogs/roof-thermal-insulation`);
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        const data = await response.json();
        return data && data.items ? data.items : [];
    } catch (error) {
        console.error("Błąd pobierania katalogu izolacji termicznej dachu:", error);
        return [];
    }
};

export const getRoofWaterproofingCatalog = async () => {
    try {
        const response = await fetch(`${API_URL}/catalogs/roof-waterproofing`);
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        const data = await response.json();
        return data && data.items ? data.items : [];
    } catch (error) {
        console.error("Błąd pobierania katalogu izolacji przeciwwodnej dachu:", error);
        return [];
    }
};

export const exportIfc = async (params) => {
    try {
        const response = await fetch(`${API_URL}/export/ifc`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const w = params.width || 0;
        const l = params.length || 0;
        a.download = `hala_${w}x${l}.ifc`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        return true;
    } catch (error) {
        console.error("Błąd eksportu do IFC:", error);
        alert("Nie udało się wyeksportować modelu do formatu IFC.");
        return false;
    }
};

export const downloadPriceCatalog = async () => {
    try {
        const response = await fetch(`${API_URL}/catalogs/prices/download`);
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "price_catalog.xlsx";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        return true;
    } catch (error) {
        console.error("Błąd pobierania cennika:", error);
        alert("Nie udało się pobrać pliku cennika.");
        return false;
    }
};

// Wgrywa zedytowany lokalnie plik cennika (File z <input type="file">) z powrotem na serwer.
// Zwraca { ok: true, summary } albo { ok: false, error } — komunikat do pokazania użytkownikowi.
export const uploadPriceCatalog = async (file) => {
    try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_URL}/catalogs/prices/upload`, {
            method: 'POST',
            body: formData,
        });
        const data = await response.json().catch(() => null);
        if (!response.ok) {
            const detail = (data && data.detail) || `Błąd HTTP: ${response.status}`;
            return { ok: false, error: detail };
        }
        return { ok: true, summary: data };
    } catch (error) {
        console.error("Błąd wgrywania cennika:", error);
        return { ok: false, error: "Nie udało się połączyć z serwerem." };
    }
};

export const exportTakeoff = async (params) => {
    try {
        const response = await fetch(`${API_URL}/quantity-takeoff/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const w = params.width || 0;
        const l = params.length || 0;
        a.download = `przedmiar_hala_${w}x${l}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        return true;
    } catch (error) {
        console.error("Błąd eksportu przedmiaru:", error);
        alert("Nie udało się wyeksportować przedmiaru do Excela.");
        return false;
    }
};

// --- Flagi funkcji / panel administratora ---

export const getFeatures = async () => {
    try {
        const response = await fetch(`${API_URL}/features`);
        if (!response.ok) throw new Error(`Błąd HTTP: ${response.status}`);
        const data = await response.json();
        return (data && data.flags) || {};
    } catch (error) {
        console.error("Błąd pobierania flag funkcji:", error);
        // W razie awarii endpointu domyślnie NIE ukrywamy funkcji — brak połączenia
        // z backendem i tak zablokuje wszystko inne w aplikacji.
        return {};
    }
};

// Weryfikuje token administratora. Zwraca { ok, labels } albo { ok: false, error }.
export const verifyAdminToken = async (token) => {
    try {
        const response = await fetch(`${API_URL}/admin/verify`, {
            method: 'POST',
            headers: { 'X-Admin-Token': token },
        });
        const data = await response.json().catch(() => null);
        if (!response.ok) {
            return { ok: false, error: (data && data.detail) || `Błąd HTTP: ${response.status}` };
        }
        return { ok: true, labels: (data && data.labels) || {} };
    } catch (error) {
        console.error("Błąd weryfikacji tokenu administratora:", error);
        return { ok: false, error: "Nie udało się połączyć z serwerem." };
    }
};

// Ustawia jedną flagę funkcji. Zwraca { ok, flags } albo { ok: false, error }.
export const setFeatureFlag = async (token, name, value) => {
    try {
        const response = await fetch(`${API_URL}/admin/features`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Admin-Token': token },
            body: JSON.stringify({ name, value }),
        });
        const data = await response.json().catch(() => null);
        if (!response.ok) {
            return { ok: false, error: (data && data.detail) || `Błąd HTTP: ${response.status}` };
        }
        return { ok: true, flags: (data && data.flags) || {} };
    } catch (error) {
        console.error("Błąd zapisu flagi funkcji:", error);
        return { ok: false, error: "Nie udało się połączyć z serwerem." };
    }
};