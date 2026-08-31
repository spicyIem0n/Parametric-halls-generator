import io
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models import HallParameters
from generators.hall_generator import HallGenerator
from core.grid_system import GridSystem3D
from core.clash_detector import ClashDetector
from core.takeoff_calculator import TakeoffCalculator
from core.insulation_catalog import load_thermal_insulation_catalog, load_waterproofing_catalog
from core.roof_load_calculator import RoofLoadCalculator
from core.foundation_sizing_calculator import FoundationSizingCalculator
from core.soil_catalog import load_soil_catalog

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


@app.get("/catalogs/roof-thermal-insulation")
def roof_thermal_insulation_catalog():
    """Katalog materiałów izolacji termicznej dachu (wczytywany z pliku Excel)."""
    return {"items": load_thermal_insulation_catalog()}


@app.get("/catalogs/roof-waterproofing")
def roof_waterproofing_catalog():
    """Katalog materiałów izolacji przeciwwodnej dachu (wczytywany z pliku Excel)."""
    return {"items": load_waterproofing_catalog()}


@app.post("/roof-loads")
def roof_loads(params: HallParameters):
    """Zebranie obciążeń dachu (wartości charakterystyczne) per moduł/hala."""
    return RoofLoadCalculator.compute(params)


@app.post("/foundation-sizing")
def foundation_sizing(params: HallParameters):
    """Automatyczny dobór gabarytów stóp fundamentowych (wartości orientacyjne)."""
    return FoundationSizingCalculator.compute(params)


@app.get("/catalogs/soil")
def soil_catalog():
    """Katalog typowych gruntów z orientacyjnym qdop (wczytywany z pliku Excel)."""
    return {"items": load_soil_catalog()}


@app.post("/quantity-takeoff")
def quantity_takeoff(params: HallParameters):
    """Zwraca przedmiar ilosciowy (lista pozycji) na podstawie modelu."""
    return {"items": TakeoffCalculator.compute(params)}


@app.post("/quantity-takeoff/export")
def quantity_takeoff_export(params: HallParameters):
    """Eksportuje przedmiar do pliku Excel (.xlsx)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    items = TakeoffCalculator.compute(params)

    wb = Workbook()
    ws = wb.active
    ws.title = "Przedmiar"

    headers = ["L.p.", "Opis pozycji", "Jednostka miary", "Ilość",
               "Cena jednostkowa", "Wartość", "Uwagi"]

    header_font = Font(bold=True, color="FFFFFF", size=10)
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=1 + col - 1, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    for r, it in enumerate(items, start=2):
        row_vals = [
            it["lp"], it["opis"], it["jednostka"], it["ilosc"],
            it["cena_jedn"], it["wartosc"], it["uwagi"],
        ]
        for c, val in enumerate(row_vals, start=1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.border = border
            if c in (1, 3, 4, 5, 6):
                cell.alignment = center
            else:
                cell.alignment = left

    # Szerokosci kolumn
    widths = [6, 42, 14, 12, 16, 14, 26]
    from openpyxl.utils import get_column_letter
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    fname = f"przedmiar_hala_{int(params.width)}x{int(params.length)}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


# Aby uruchomić: uvicorn main:app --reload
