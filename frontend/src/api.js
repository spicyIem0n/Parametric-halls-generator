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