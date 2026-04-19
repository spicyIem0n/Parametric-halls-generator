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
        angle_rad = math.radians(params.roof_angle)
        
        for i in range(num_frames):
            z_pos = i * params.bay_spacing - (params.length / 2)
            
            for j in range(params.number_of_aisles + 1):
                x_pos = -params.width / 2 + j * (params.width / params.number_of_aisles)
                
                # Czy to ściana zewnętrzna lewa czy prawa?
                is_left_ext = (j == 0)
                is_right_ext = (j == params.number_of_aisles)
                is_external = is_left_ext or is_right_ext
                
                # Czy w tej konkretnej osi jest aktywny dok?
                is_dock_here = (is_left_ext and params.left_dock_zone) or (is_right_ext and params.right_dock_zone)
                
                # 1. Określenie typu
                if is_external:
                    c_type = "external_dock" if is_dock_here else "external_main"
                else:
                    c_type = "internal_dock" if is_dock_here else "internal_main"
                
                # 2. Pobranie przekroju słupa
                if params.column_method == "manual":
                    section = params.manual_column_sections.get(c_type, ColumnFactory.DEFAULT_SECTIONS[c_type])
                else:
                    section = ColumnFactory.DEFAULT_SECTIONS[c_type]
                
                # 3. Pobranie grubości stopy, na której stoi słup
                if params.foundation_method == "manual":
                    f_size = params.manual_sizes.get(c_type, FoundationFactory.DEFAULT_SIZES[c_type])
                else:
                    f_size = FoundationFactory.DEFAULT_SIZES[c_type]
                
                f_thickness = f_size[2]
                f_depth_level = params.dock_foundation_depth if is_dock_here else params.foundation_depth
                
                # 4. Obliczanie wysokości spodu dźwigara w tym punkcie X
                dist_from_center = abs(x_pos)
                roof_top_y = params.clear_height + ((params.width / 2 - dist_from_center) * math.tan(angle_rad))
                
                # 5. Obliczanie wysokości słupa
                # Zwróć uwagę, że posadzka zajmuje przestrzeń od 0 do -floor_thickness.
                # Słup musi przenikać przez posadzkę, opierając się na fundamencie.
                column_base_y = -f_depth_level + f_thickness
                column_height = roof_top_y - column_base_y
                
                columns.append(Component3D(
                    type="column",
                    position=[x_pos, column_base_y + (column_height / 2), z_pos],
                    rotation=[0, 0, 0],
                    scale=[section[0], column_height, section[1]]
                ))
                
        return columns