import math
from models import Component3D, HallParameters

# --- FUNKCJE POMOCNICZE DO GENEROWANIA ELEMENTÓW PRĘTOWYCH ---

def _get_xy_member(pt1, pt2, type_name, t1, t2):
    """Generuje pręt w płaszczyźnie ramy głównej (XY)"""
    x1, y1, z1 = pt1
    x2, y2, z2 = pt2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 0.01: return None
    
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    angle = math.atan2(dy, dx)
    return Component3D(type=type_name, position=[cx, cy, z1], rotation=[0, 0, angle], scale=[length, t1, t2])

def _get_zy_member(pt1, pt2, type_name, t1, t2):
    """Generuje pręt w płaszczyźnie dachu wzdłuż hali (ZY - dla płatwi)"""
    x1, y1, z1 = pt1
    x2, y2, z2 = pt2
    dy, dz = y2 - y1, z2 - z1
    length = math.hypot(dz, dy)
    if length < 0.01: return None
    
    cy, cz = (y1 + y2) / 2, (z1 + z2) / 2
    # Obrót wokół osi X dla płaszczyzny podłużnej
    angle = math.atan2(-dy, dz) 
    return Component3D(type=type_name, position=[x1, cy, cz], rotation=[angle, 0, 0], scale=[t1, t2, length])

def _build_truss(nodes_top, nodes_bot, type_chord, type_web, t_chord, t_web, is_xy_plane):
    """Generuje kompletną kratownicę (pasy, słupki, zastrzały) na podstawie siatki węzłów"""
    elements = []
    n = len(nodes_top)
    
    for i in range(n - 1):
        # 1. Pasy (Górny i Dolny)
        if is_xy_plane:
            elements.append(_get_xy_member(nodes_top[i], nodes_top[i+1], type_chord, t_chord, t_chord))
            # Pas dolny generujemy tylko jeśli nie jest zbieżny z górnym (podpora)
            if abs(nodes_bot[i][1] - nodes_top[i][1]) > 0.05 or abs(nodes_bot[i+1][1] - nodes_top[i+1][1]) > 0.05:
                elements.append(_get_xy_member(nodes_bot[i], nodes_bot[i+1], type_chord, t_chord, t_chord))
        else:
            elements.append(_get_zy_member(nodes_top[i], nodes_top[i+1], type_chord, t_chord, t_chord))
            if abs(nodes_bot[i][1] - nodes_top[i][1]) > 0.05 or abs(nodes_bot[i+1][1] - nodes_top[i+1][1]) > 0.05:
                elements.append(_get_zy_member(nodes_bot[i], nodes_bot[i+1], type_chord, t_chord, t_chord))
                
        # 2. Zastrzały (Układ typu Warren)
        diag_start = nodes_bot[i] if i % 2 == 0 else nodes_top[i]
        diag_end = nodes_top[i+1] if i % 2 == 0 else nodes_bot[i+1]
            
        dist = math.sqrt(sum((a-b)**2 for a,b in zip(diag_start, diag_end)))
        if dist > 0.1:
            if is_xy_plane:
                elements.append(_get_xy_member(diag_start, diag_end, type_web, t_web, t_web))
            else:
                elements.append(_get_zy_member(diag_start, diag_end, type_web, t_web, t_web))

    # 3. Słupki pionowe
    for i in range(1, n - 1):
        dist = abs(nodes_bot[i][1] - nodes_top[i][1])
        if dist > 0.1:
            if is_xy_plane:
                elements.append(_get_xy_member(nodes_bot[i], nodes_top[i], type_web, t_web, t_web))
            else:
                elements.append(_get_zy_member(nodes_bot[i], nodes_top[i], type_web, t_web, t_web))
                
    return [e for e in elements if e is not None]

# --- FABRYKA DACHU ---

class RoofFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        elements = []
        num_frames = int(params.length // params.bay_spacing) + 1
        half_width = params.width / 2
        
        # Parametry techniczne
        col_w = 0.5 
        wall_t = params.cladding_thickness # BŁĄD USUNIĘTY: właściwa nazwa zmiennej z models.py
        chord_t, web_t = 0.15, 0.08
        purlin_chord_t, purlin_web_t = 0.1, 0.06
        
        # Obliczamy wysunięcie dachu do lica zewnętrznego (osie + połowa słupa + płyta)
        ext_roof_half_width = half_width + (col_w / 2) + wall_t
        
        # 1. SIATKA WĘZŁÓW X (Synchronizacja dla całego dachu)
        # Używamy math.ceil - rzeczywisty rozstaw zawsze będzie <= zadanemu (bezpieczne dla płyt warstwowych)
        # Zabezpieczenie przed zerem w rozstawie
        safe_spacing = max(1.0, params.purlin_spacing)
        num_purlins_per_side = max(1, math.ceil(half_width / safe_spacing))
        # Tworzymy listę pozycji X, gdzie będą węzły (osie płatwi)
        xs = []
        for p in range(num_purlins_per_side + 1):
            xs.append(-half_width + (p * (half_width / num_purlins_per_side)))
        for p in range(1, num_purlins_per_side + 1):
            xs.append((p * (half_width / num_purlins_per_side)))
        xs = sorted(list(set(xs)))

        angle_rad = math.radians(params.roof_angle) if params.roof_drainage_type == "gravity" else 0
        
        # --- ETAP 1: DŹWIGARY GŁÓWNE ---
        for i in range(num_frames):
            z_pos = i * params.bay_spacing - (params.length / 2)
            nodes_top, nodes_bot = [], []
            
            for j, x in enumerate(xs):
                # Wysokość górna
                if params.roof_drainage_type == "gravity":
                    y_top = params.clear_height + params.truss_depth + (half_width - abs(x)) * math.tan(angle_rad)
                else:
                    y_top = params.clear_height + params.truss_depth
                
                # Wysokość dolna (zbieżna na podporach)
                if j == 0 or j == len(xs) - 1:
                    y_bot = y_top
                else:
                    if params.roof_drainage_type == "gravity":
                        y_bot = params.clear_height + (half_width - abs(x)) * math.tan(angle_rad)
                    else:
                        y_bot = params.clear_height
                
                nodes_top.append((x, y_top, z_pos))
                nodes_bot.append((x, y_bot, z_pos))
            
            elements.extend(_build_truss(nodes_top, nodes_bot, "truss_chord", "truss_web", chord_t, web_t, True))
            
        # --- ETAP 2: PŁATWIE KRATOWE ---
        purlin_depth = params.truss_depth * 0.5
        for i in range(num_frames - 1):
            z_start = i * params.bay_spacing - (params.length / 2)
            # Podział płatwi na 4 pola kratowe dla lepszego wyglądu
            zs = [z_start + k * (params.bay_spacing / 4) for k in range(5)]
            
            for x in xs:
                nodes_top_p, nodes_bot_p = [], []
                # Baza Y zależy od pozycji X na dźwigarze
                if params.roof_drainage_type == "gravity":
                    base_y_top = params.clear_height + params.truss_depth + (half_width - abs(x)) * math.tan(angle_rad)
                else:
                    base_y_top = params.clear_height + params.truss_depth
                    
                for k, z in enumerate(zs):
                    y_top = base_y_top
                    # Płatew zbieżna na oparciu o dźwigar
                    y_bot = y_top if (k == 0 or k == len(zs) - 1) else y_top - purlin_depth
                    nodes_top_p.append((x, y_top, z))
                    nodes_bot_p.append((x, y_bot, z))
                
                elements.extend(_build_truss(nodes_top_p, nodes_bot_p, "purlin", "purlin_strut", purlin_chord_t, purlin_web_t, False))

        # --- ETAP 3: POSZYCIE DACHOWE (Dociągnięte do lica zewnętrznego) ---
        if params.roof_drainage_type == "gravity":
            chord_len_ext = ext_roof_half_width / math.cos(angle_rad)
            # Środek panelu musi uwzględniać przesunięcie lica
            panel_x = ext_roof_half_width / 2
            roof_y = params.clear_height + params.truss_depth + (ext_roof_half_width / 2) * math.tan(angle_rad) + (params.roof_panel_thickness / 2)
            
            elements.append(Component3D(type="roof_panel", position=[-panel_x, roof_y, 0], rotation=[0, 0, -angle_rad], scale=[chord_len_ext, params.roof_panel_thickness, params.length]))
            elements.append(Component3D(type="roof_panel", position=[panel_x, roof_y, 0], rotation=[0, 0, angle_rad], scale=[chord_len_ext, params.roof_panel_thickness, params.length]))
            
        elif params.roof_drainage_type == "vacuum":
            # Przywrócona pełna logika instalacji podciśnieniowej i spadków kopertowych
            top_y = params.clear_height + params.truss_depth
            slope_factor = params.roof_slope_percent / 100.0
            inlets = []
            
            # Parametry stref zlewni
            zone_w = params.width / params.drainage_zones_x
            zone_l = params.length / params.drainage_zones_z
            
            # 1. Generowanie wpustów dachowych
            for ix in range(params.drainage_zones_x):
                for iz in range(params.drainage_zones_z):
                    inlet_x = -half_width + (ix * zone_w) + (zone_w / 2)
                    inlet_z = -params.length/2 + (iz * zone_l) + (zone_l / 2)
                    inlets.append((inlet_x, inlet_z))
                    elements.append(Component3D(type="drainage_inlet", position=[inlet_x, top_y + 0.15, inlet_z], rotation=[0, 0, 0], scale=[0.4, 0.3, 0.4]))

            # 2. Tworzenie "kopert" ze spadkami
            # Rozszerzamy siatkę X o lica zewnętrzne, aby dach przykrył attykę
            panel_xs = [-ext_roof_half_width] + [x for x in xs if -ext_roof_half_width < x < ext_roof_half_width] + [ext_roof_half_width]
            panel_xs = sorted(list(set(panel_xs)))

            for i in range(num_frames - 1):
                z1 = i * params.bay_spacing - (params.length / 2)
                z2 = (i + 1) * params.bay_spacing - (params.length / 2)
                z_mid = (z1 + z2) / 2
                
                for p in range(len(panel_xs) - 1):
                    x1 = panel_xs[p]
                    x2 = panel_xs[p+1]
                    panel_w = x2 - x1
                    x_mid = (x1 + x2) / 2
                    
                    # Szukanie najbliższego wpustu (odległość taksówkowa)
                    min_dist = float('inf')
                    for (ix, iz) in inlets:
                        dist = abs(x_mid - ix) + abs(z_mid - iz)
                        if dist < min_dist:
                            min_dist = dist
                            
                    height_offset = min_dist * slope_factor
                    purlin_base_y = top_y
                    
                    # Słupek dystansowy (styropian spadkowy / podniesienie płatwi)
                    elements.append(Component3D(type="purlin_strut", position=[x_mid, purlin_base_y + height_offset/2, z_mid], rotation=[0, 0, 0], scale=[0.05, height_offset, 0.05]))
                    
                    # Połać dachu ze spadkiem
                    purlin_y = purlin_base_y + height_offset
                    elements.append(Component3D(type="roof_panel", position=[x_mid, purlin_y + params.roof_panel_thickness/2, z_mid], rotation=[0, 0, 0], scale=[panel_w, params.roof_panel_thickness, params.bay_spacing]))

        return elements