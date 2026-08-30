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