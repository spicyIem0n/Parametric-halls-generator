from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import HallParameters
from generators.hall_generator import HallGenerator
from core.grid_system import GridSystem3D
from core.clash_detector import ClashDetector

app = FastAPI(title="Parametric Hall API")

# Konfiguracja CORS (niezbędne dla połączenia z Reactem)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji zamień na domenę frontendu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate-hall")
def generate_hall(params: HallParameters):
    """Generuje pełną geometrię 3D hali na podstawie parametrów."""
    generator = HallGenerator(params)
    components = generator.generate_all_components()
    return {"components": components}


@app.post("/validate-hall")
def validate_hall(params: HallParameters):
    """
    Waliduje model hali pod kątem kolizji geometrycznych.
    Zwraca listę ostrzeżeń i błędów (clashów).
    """
    if params.hall_type == "complex":
        # Dla hal złożonych — walidacja per blok
        all_clashes = []
        for block in (params.blocks or []):
            block_dict = params.model_dump()
            block_dict.update({
                "hall_type": "simple",
                "width": block.width, "length": block.length,
                "clear_height": block.clear_height, "bay_spacing": block.bay_spacing,
                "roof_angle": block.roof_angle, "roof_drainage_type": block.roof_drainage_type,
                "number_of_aisles": block.number_of_aisles,
                "docks_config": {}, "blocks": [], "fire_walls": [],
                "technical_rooms": [], "external_offices": [],
                "internal_offices": [], "office_reserve_zones": [],
            })
            block_params = HallParameters(**block_dict)
            grid = GridSystem3D(block_params)
            block_params.length = grid.length
            detector = ClashDetector(grid, block_params)
            result = detector.validate()
            for clash in result.clashes:
                clash.message = f"[{block.block_id}] {clash.message}"
            all_clashes.extend(result.clashes)

        errors = [c for c in all_clashes if c.severity == "error"]
        return {
            "is_valid": len(errors) == 0,
            "warnings_count": len(all_clashes) - len(errors),
            "errors_count": len(errors),
            "clashes": [
                {"clash_type": c.clash_type, "severity": c.severity, "message": c.message,
                 "element_a": c.element_a_type, "element_b": c.element_b_type,
                 "position": c.position, "bay_index": c.bay_index, "side": c.side}
                for c in all_clashes
            ],
        }

    grid = GridSystem3D(params)
    params.length = grid.length

    detector = ClashDetector(grid, params)
    result = detector.validate()

    return result.to_dict()


# Aby uruchomić: uvicorn main:app --reload
