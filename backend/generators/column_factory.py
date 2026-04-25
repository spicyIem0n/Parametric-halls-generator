import math
from models import Component3D, HallParameters
from .foundation_factory import FoundationFactory

class ColumnFactory:
    DEFAULT_SECTIONS = {
        "external_main": [0.4, 0.4],
        "internal_main": [0.4, 0.4],
        "intermediate_cladding": [0.3, 0.3],
        "external_dock": [0.5, 0.5],
        "internal_dock": [0.5, 0.5]
    }

    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        columns = []
        num_frames = int(params.length // params.bay_spacing) + 1
        angle_rad = math.radians(params.roof_angle) if params.roof_drainage_type == "gravity" else 0
        
        for i in range(num_frames):
            z_pos = i * params.bay_spacing - (params.length / 2)
            is_gable_frame = (i == 0 or i == num_frames - 1) # Czy to pierwsza lub ostatnia oś (ściana szczytowa)
            
            # --- GENEROWANIE SŁUPÓW GŁÓWNYCH DLA KAŻDEJ NAWY ---
            for j in range(params.number_of_aisles + 1):
                x_pos = -params.width / 2 + j * (params.width / params.number_of_aisles)
                
                is_left_ext = (j == 0)
                is_right_ext = (j == params.number_of_aisles)
                is_external = is_left_ext or is_right_ext
                
                # Odczyt z nowej mapy doków (dla lewej lub prawej ściany w przęśle 'i')
                is_dock_here = False
                if is_left_ext and params.docks_config.get(f"left-{i}") == "dock":
                    is_dock_here = True
                elif is_right_ext and params.docks_config.get(f"right-{i}") == "dock":
                    is_dock_here = True
                
                if is_external:
                    c_type = "external_dock" if is_dock_here else "external_main"
                else:
                    c_type = "internal_dock" if is_dock_here else "internal_main"
                
                if params.column_method == "manual":
                    section = params.manual_column_sections.get(c_type, ColumnFactory.DEFAULT_SECTIONS[c_type])
                else:
                    section = ColumnFactory.DEFAULT_SECTIONS[c_type]
                
                if params.foundation_method == "manual":
                    f_size = params.manual_sizes.get(c_type, FoundationFactory.DEFAULT_SIZES[c_type])
                else:
                    f_size = FoundationFactory.DEFAULT_SIZES[c_type]
                
                f_thickness = f_size[2]
                f_depth_level = params.dock_foundation_depth if is_dock_here else params.foundation_depth
                
                # Nowa logika: Obliczanie dokładnej wysokości pasa górnego w tym punkcie X
                dist_from_center = abs(x_pos)
                if params.roof_drainage_type == "gravity":
                    roof_top_y = params.clear_height + params.truss_depth + ((params.width / 2 - dist_from_center) * math.tan(angle_rad))
                else:
                    roof_top_y = params.clear_height + params.truss_depth
                    
                column_base_y = -f_depth_level + f_thickness
                column_height = roof_top_y - column_base_y
                
                # Dodanie słupa głównego
                columns.append(Component3D(
                    type="column",
                    position=[x_pos, column_base_y + (column_height / 2), z_pos],
                    rotation=[0, 0, 0],
                    scale=[section[0], column_height, section[1]]
                ))
                
                # --- GENEROWANIE SŁUPÓW SZCZYTOWYCH (WIATROWYCH) ---
                # Słupy szczytowe wstawiamy tylko na ramach skrajnych, równomiernie MIĘDZY głównymi osiami
                if is_gable_frame and j < params.number_of_aisles:
                    aisle_width = params.width / params.number_of_aisles
                    num_gable_cols = max(1, int(aisle_width // 6)) # Wstaw słup wiatrowy ok. co 6 metrów wewnątrz nawy
                    
                    if num_gable_cols > 0:
                        step = aisle_width / (num_gable_cols + 1)
                        for k in range(1, num_gable_cols + 1):
                            gx_pos = x_pos + k * step
                            dist_from_center_g = abs(gx_pos)
                            
                            # Rzędna dachu w miejscu słupka wiatrowego
                            if params.roof_drainage_type == "gravity":
                                g_roof_top_y = params.clear_height + params.truss_depth + ((params.width / 2 - dist_from_center_g) * math.tan(angle_rad))
                            else:
                                g_roof_top_y = params.clear_height + params.truss_depth
                                
                            g_base_y = -params.foundation_depth + 0.40 # Uproszczony fundament wiatrowy
                            g_height = g_roof_top_y - g_base_y
                            
                            columns.append(Component3D(
                                type="column",
                                position=[gx_pos, g_base_y + (g_height / 2), z_pos],
                                rotation=[0, 0, 0],
                                scale=[0.3, g_height, 0.3] # Mniejszy przekrój dla słupków wiatrowych
                            ))
                            
        return columns