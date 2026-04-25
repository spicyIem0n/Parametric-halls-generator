import math
from models import Component3D, HallParameters

class CladdingFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        elements = []
        
        # Parametry pomocnicze
        col_w = 0.5  # Przyjmujemy szerokość słupa (zgodnie z ColumnFactory)
        half_w = params.width / 2
        half_l = params.length / 2
        
        # 1. Obliczamy pozycję lica zewnętrznego słupa
        ext_face_x = half_w + (col_w / 2)
        ext_face_z = half_l + (col_w / 2)
        
        # 2. Wyliczenie wysokości attyki (zgodnie z poprzednią poprawką)
        if params.roof_drainage_type == "gravity":
            angle_rad = math.radians(params.roof_angle)
            max_roof_h = params.clear_height + params.truss_depth + (params.width / 2) * math.tan(angle_rad)
        else:
            slope_factor = params.roof_slope_percent / 100.0
            max_drain_dist = (params.width / params.drainage_zones_x / 2) + (params.length / params.drainage_zones_z / 2)
            max_roof_h = params.clear_height + params.truss_depth + (max_drain_dist * slope_factor)
        
        parapet_h = max_roof_h + 0.20
        t = params.cladding_thickness # Pobieranie właściwej grubości z interfejsu
        # --- ŚCIANY WZDŁUŻNE (Longitudinal) ---
        # Przesuwamy o lico zewnętrzne + połowa grubości płyty
        cladding_x = ext_face_x + (t / 2)
        elements.append(Component3D(type="sandwich_panel", position=[-cladding_x, parapet_h/2, 0], rotation=[0,0,0], scale=[t, parapet_h, params.length]))
        elements.append(Component3D(type="sandwich_panel", position=[cladding_x, parapet_h/2, 0], rotation=[0,0,0], scale=[t, parapet_h, params.length]))
        
        # --- ŚCIANY SZCZYTOWE (Gable) ---
        # Ściana szczytowa musi zakryć lico słupów i krawędzie płyt bocznych
        total_ext_width = (ext_face_x + t) * 2
        cladding_z = ext_face_z + (t / 2)
        
        elements.append(Component3D(type="sandwich_panel", position=[0, parapet_h/2, -cladding_z], rotation=[0,0,0], scale=[total_ext_width, parapet_h, t]))
        elements.append(Component3D(type="sandwich_panel", position=[0, parapet_h/2, cladding_z], rotation=[0,0,0], scale=[total_ext_width, parapet_h, t]))
        
        return elements