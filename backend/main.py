from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import HallParameters
from generators.hall_generator import HallGenerator

app = FastAPI(title="Parametric Hall API")

# Konfiguracja CORS (niezbędne dla połączenia z Reactem)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # W produkcji zamień na domenę frontendu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-hall")
def generate_hall(params: HallParameters):
    # Inicjalizacja głównego generatora z przekazanymi parametrami
    generator = HallGenerator(params)
    
    # Obliczenie pełnej geometrii
    components = generator.generate_all_components()
    
    # Zwrócenie wygenerowanej listy komponentów do frontendu
    return {"components": components}

# Aby uruchomić: uvicorn main:app --reload