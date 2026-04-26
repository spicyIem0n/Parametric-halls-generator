import math
from models import Component3D, HallParameters

def _build_wall_with_hole(x, z_center, bay_len, t, parapet_h, hole_w, hole_h, hole_y_start):
    """Zestawia ścianę z paneli omijając otwór na dok/bramę"""
    pieces = []
    # 1. Lewy i prawy panel boczny
    side_w = (bay_len - hole_w) / 2
    if side_w > 0:
        pieces.append(Component3D(type="sandwich_panel", position=[x, parapet_h/2, z_center - bay_len/2 + side_w/2], rotation=[0,0,0], scale=[t, parapet_h, side_w]))
        pieces.append(Component3D(type="sandwich_panel", position=[x, parapet_h/2, z_center + bay_len/2 - side_w/2], rotation=[0,0,0], scale=[t, parapet_h, side_w]))
    
    # 2. Górny panel (nad otworem do attyki)
    hole_top = hole_y_start + hole_h
    top_h = parapet_h - hole_top
    if top_h > 0:
        pieces.append(Component3D(type="sandwich_panel", position=[x, hole_top + top_h/2, z_center], rotation=[0,0,0], scale=[t, top_h, hole_w]))
    
    # 3. Dolny panel (pod dokiem, zwykle pełniący rolę oparcia rampy od poz 0.0 do 1.2m)
    if hole_y_start > 0:
        pieces.append(Component3D(type="sandwich_panel", position=[x, hole_y_start/2, z_center], rotation=[0,0,0], scale=[t, hole_y_start, hole_w]))
        
    return pieces

class CladdingFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        elements = []
        col_w = 0.5 
        t = params.cladding_thickness 
        half_w = params.width / 2
        half_l = params.length / 2
        
        ext_face_x = half_w + (col_w / 2)
        ext_face_z = half_l + (col_w / 2)
        
        if params.roof_drainage_type == "gravity":
            angle_rad = math.radians(params.roof_angle)
            max_roof_h = params.clear_height + params.truss_depth + (params.width / 2) * math.tan(angle_rad)
        else:
            slope_factor = params.roof_slope_percent / 100.0
            max_drain_dist = (params.width / params.drainage_zones_x / 2) + (params.length / params.drainage_zones_z / 2)
            max_roof_h = params.clear_height + params.truss_depth + (max_drain_dist * slope_factor)
        
        parapet_h = max_roof_h + 0.20
        cladding_x = ext_face_x + (t / 2)

        # --- ŚCIANY WZDŁUŻNE ---
        num_frames = int(params.length // params.bay_spacing) + 1
        slots_per_bay = max(1, int(params.bay_spacing // 4.0))
        slot_w = params.bay_spacing / slots_per_bay

        for i in range(num_frames - 1):
            bay_z_start = (i * params.bay_spacing) - (params.length / 2)
            for k in range(slots_per_bay):
                z_center = bay_z_start + (k * slot_w) + (slot_w / 2)
                
                left_type = params.docks_config.get(f"left-{i}-{k}", "none")
                if left_type == "dock": elements.extend(_build_wall_with_hole(-cladding_x, z_center, slot_w, t, parapet_h, 3.0, 3.0, 0.0))
                elif left_type == "gate": elements.extend(_build_wall_with_hole(-cladding_x, z_center, slot_w, t, parapet_h, 4.0, 4.0, 0.0))
                else: elements.append(Component3D(type="sandwich_panel", position=[-cladding_x, parapet_h/2, z_center], rotation=[0,0,0], scale=[t, parapet_h, slot_w]))

                right_type = params.docks_config.get(f"right-{i}-{k}", "none")
                if right_type == "dock": elements.extend(_build_wall_with_hole(cladding_x, z_center, slot_w, t, parapet_h, 3.0, 3.0, 0.0))
                elif right_type == "gate": elements.extend(_build_wall_with_hole(cladding_x, z_center, slot_w, t, parapet_h, 4.0, 4.0, 0.0))
                else: elements.append(Component3D(type="sandwich_panel", position=[cladding_x, parapet_h/2, z_center], rotation=[0,0,0], scale=[t, parapet_h, slot_w]))

       # --- ZAMKNIĘCIE NAROŻNIKÓW (SZCZYTY) ---
        # Poszerzamy panel ścienny z długości, aby zasłonił lico ścian podłużnych
        total_ext_width = params.width + col_w + (2 * t) 
        
        elements.append(Component3D(
            type="sandwich_panel", 
            position=[0, parapet_h/2, -params.length/2 - col_w/2 - t/2], 
            rotation=[0,0,0], 
            scale=[total_ext_width, parapet_h, t]
        ))
        elements.append(Component3D(
            type="sandwich_panel", 
            position=[0, parapet_h/2, params.length/2 + col_w/2 + t/2], 
            rotation=[0,0,0], 
            scale=[total_ext_width, parapet_h, t]
        ))

        # UWAGA: w ścianach podłużnych zmieniamy współrzędną `slot_w` dla pierwszych/ostatnich elementów
        # To wymagałoby dużej zmiany, dla zachowania poprawności kodu zostawiamy to tak jak powyżej.
        return elements