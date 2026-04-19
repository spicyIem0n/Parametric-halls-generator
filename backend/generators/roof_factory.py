import math
from models import Component3D, HallParameters

class RoofFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        elements = []
        num_frames = int(params.length // params.bay_spacing) + 1
        half_width = params.width / 2
        chord_thickness = 0.15 

        if params.roof_drainage_type == "gravity":
            # 1. TRADYCYJNY DACH DWUSPADOWY (GRAWITACYJNY)
            angle_rad = math.radians(params.roof_angle)
            chord_length = half_width / math.cos(angle_rad)
            
            for i in range(num_frames):
                z_pos = i * params.bay_spacing - (params.length / 2)
                bottom_start_y = params.clear_height
                top_start_y = params.clear_height + params.truss_depth
                
                y_offset_mid = math.sin(angle_rad) * chord_length / 2
                
                # Kratownice (pasy dolne i górne)
                elements.append(Component3D(type="truss_chord", position=[-half_width/2, bottom_start_y + y_offset_mid, z_pos], rotation=[0, 0, -angle_rad], scale=[chord_length, chord_thickness, chord_thickness]))
                elements.append(Component3D(type="truss_chord", position=[-half_width/2, top_start_y + y_offset_mid, z_pos], rotation=[0, 0, -angle_rad], scale=[chord_length, chord_thickness, chord_thickness]))
                elements.append(Component3D(type="truss_chord", position=[half_width/2, bottom_start_y + y_offset_mid, z_pos], rotation=[0, 0, angle_rad], scale=[chord_length, chord_thickness, chord_thickness]))
                elements.append(Component3D(type="truss_chord", position=[half_width/2, top_start_y + y_offset_mid, z_pos], rotation=[0, 0, angle_rad], scale=[chord_length, chord_thickness, chord_thickness]))
                
                # Słupki kratownicy (uproszczone)
                num_struts = 6
                for s in range(1, num_struts):
                    x_strut = (s / num_struts) * half_width
                    strut_h = params.truss_depth / math.cos(angle_rad)
                    y_strut_l = bottom_start_y + ((half_width - x_strut) * math.tan(angle_rad)) + (params.truss_depth/2)
                    y_strut_r = bottom_start_y + (x_strut * math.tan(angle_rad)) + (params.truss_depth/2)
                    elements.append(Component3D(type="truss_web", position=[-x_strut, y_strut_l, z_pos], rotation=[0, 0, 0], scale=[0.08, strut_h, 0.08]))
                    elements.append(Component3D(type="truss_web", position=[x_strut, y_strut_r, z_pos], rotation=[0, 0, 0], scale=[0.08, strut_h, 0.08]))

            # Płatwie i pokrycie
            num_purlins_per_side = int(half_width // params.purlin_spacing)
            for p in range(num_purlins_per_side + 1):
                x_dist = p * params.purlin_spacing
                y_roof_level = params.clear_height + params.truss_depth + ((half_width - x_dist) * math.tan(angle_rad)) + (chord_thickness/2)
                if x_dist != half_width: 
                    elements.append(Component3D(type="purlin", position=[-half_width + x_dist, y_roof_level + 0.1, 0], rotation=[0, 0, 0], scale=[0.1, 0.2, params.length]))
                elements.append(Component3D(type="purlin", position=[x_dist, y_roof_level + 0.1, 0], rotation=[0, 0, 0], scale=[0.1, 0.2, params.length]))

            roof_panel_y = params.clear_height + params.truss_depth + (math.sin(angle_rad) * chord_length / 2) + 0.2 + (params.roof_panel_thickness / 2)
            elements.append(Component3D(type="roof_panel", position=[-half_width/2, roof_panel_y, 0], rotation=[0, 0, -angle_rad], scale=[chord_length + 0.2, params.roof_panel_thickness, params.length + 0.4]))
            elements.append(Component3D(type="roof_panel", position=[half_width/2, roof_panel_y, 0], rotation=[0, 0, angle_rad], scale=[chord_length + 0.2, params.roof_panel_thickness, params.length + 0.4]))

        elif params.roof_drainage_type == "vacuum":
            # 2. DACH PŁASKI Z ODWODNIENIEM PODCIŚNIENIOWYM (KOPERTY)
            bottom_y = params.clear_height
            top_y = params.clear_height + params.truss_depth
            slope_factor = params.roof_slope_percent / 100.0

            # Kratownice płaskie
            for i in range(num_frames):
                z_pos = i * params.bay_spacing - (params.length / 2)
                # Pas dolny i górny (ciągłe przez całą szerokość)
                elements.append(Component3D(type="truss_chord", position=[0, bottom_y, z_pos], rotation=[0, 0, 0], scale=[params.width, chord_thickness, chord_thickness]))
                elements.append(Component3D(type="truss_chord", position=[0, top_y, z_pos], rotation=[0, 0, 0], scale=[params.width, chord_thickness, chord_thickness]))
                
                # Słupki kratownicy
                num_struts = int(params.width // 2)
                for s in range(1, num_struts):
                    x_strut = -half_width + (s * (params.width / num_struts))
                    elements.append(Component3D(type="truss_web", position=[x_strut, bottom_y + params.truss_depth/2, z_pos], rotation=[0, 0, 0], scale=[0.08, params.truss_depth, 0.08]))

            # Kalkulacja położeń wpustów (niecek)
            inlets = []
            zone_w = params.width / params.drainage_zones_x
            zone_l = params.length / params.drainage_zones_z
            
            for ix in range(params.drainage_zones_x):
                for iz in range(params.drainage_zones_z):
                    inlet_x = -half_width + (ix * zone_w) + (zone_w / 2)
                    inlet_z = -params.length/2 + (iz * zone_l) + (zone_l / 2)
                    inlets.append((inlet_x, inlet_z))
                    # Wygenerowanie wizualnego wpustu podciśnieniowego (niebieski cylinder/box)
                    elements.append(Component3D(type="drainage_inlet", position=[inlet_x, top_y + 0.15, inlet_z], rotation=[0, 0, 0], scale=[0.4, 0.3, 0.4]))

            # Tworzenie "kopert": Segmentacja płatwi i podnoszenie ich na słupkach
            num_purlins = int(params.width // params.purlin_spacing) + 1
            
            for i in range(num_frames - 1):
                z1 = i * params.bay_spacing - (params.length / 2)
                z2 = (i + 1) * params.bay_spacing - (params.length / 2)
                z_mid = (z1 + z2) / 2
                
                for p in range(num_purlins):
                    x1 = -half_width + p * params.purlin_spacing
                    x2 = min(-half_width + (p+1) * params.purlin_spacing, half_width)
                    if x2 <= x1: continue
                    
                    panel_w = x2 - x1
                    x_mid = (x1 + x2) / 2
                    
                    # Obliczanie dystansu do NAJBLIŻSZEGO wpustu (odległość miejska do kosza)
                    min_dist = float('inf')
                    for (ix, iz) in inlets:
                        dist = abs(x_mid - ix) + abs(z_mid - iz)
                        if dist < min_dist:
                            min_dist = dist
                            
                    # Podniesienie na słupku = dystans * spadek
                    height_offset = min_dist * slope_factor
                    purlin_base_y = top_y + chord_thickness/2
                    
                    # Słupek dystansowy z kratownicy do płatwi
                    elements.append(Component3D(type="purlin_strut", position=[x_mid, purlin_base_y + height_offset/2, z_mid], rotation=[0, 0, 0], scale=[0.05, height_offset + 0.05, 0.05]))
                    
                    # Fragment płatwi
                    purlin_y = purlin_base_y + height_offset
                    elements.append(Component3D(type="purlin", position=[x_mid, purlin_y + 0.1, z_mid], rotation=[0, 0, 0], scale=[panel_w, 0.2, params.bay_spacing]))
                    
                    # Fragment poszycia dachowego (powłoka łamana)
                    elements.append(Component3D(type="roof_panel", position=[x_mid, purlin_y + 0.2 + params.roof_panel_thickness/2, z_mid], rotation=[0, 0, 0], scale=[panel_w, params.roof_panel_thickness, params.bay_spacing]))

        return elements