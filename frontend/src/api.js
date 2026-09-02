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