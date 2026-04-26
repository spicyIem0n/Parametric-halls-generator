import math
from models import Component3D, HallParameters

class ColumnFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        columns = []
        num_frames = int(params.length // params.bay_spacing) + 1
        half_width = params.width / 2

        manual_sections = params.manual_column_sections if params.manual_column_sections else {}
        docks_config = params.docks_config if params.docks_config else {}

        sec_ext_main = manual_sections.get("external_main", [0.4, 0.4]) if params.column_method == "manual" else [0.4, 0.4]
        sec_int_main = manual_sections.get("internal_main", [0.4, 0.4]) if params.column_method == "manual" else [0.4, 0.4]
        sec_int_clad = manual_sections.get("intermediate_cladding", [0.3, 0.3]) if params.column_method == "manual" else [0.3, 0.3]

        slots_per_bay = max(1, int(params.bay_spacing // 4.0))

        # 1. SŁUPY RAM GŁÓWNYCH
        for i in range(num_frames):
            z_pos = i * params.bay_spacing - (params.length / 2)
            
            # Tworzenie siatki osi w poprzek ramy (uwzględnia nawy pośrednie)
            xs = [-half_width]
            if params.number_of_aisles > 1:
                aisle_width = params.width / params.number_of_aisles
                for j in range(1, params.number_of_aisles):
                    xs.append(-half_width + j * aisle_width)
            xs.append(half_width)

            for x_pos in xs:
                is_left_ext = (x_pos == -half_width)
                is_right_ext = (x_pos == half_width)
                is_external = is_left_ext or is_right_ext

                section = sec_ext_main if is_external else sec_int_main
                
                angle_rad = math.radians(params.roof_angle) if params.roof_drainage_type == "gravity" else 0
                h_roof = params.clear_height + params.truss_depth + (half_width - abs(x_pos)) * math.tan(angle_rad)
                
                # POPRAWKA 2: Słupy wewnętrzne dociągamy do pasa górnego dźwigara
                column_top_y = h_roof
                
                depth = params.foundation_depth
                side_str = "left" if is_left_ext else ("right" if is_right_ext else None)
                if side_str:
                    dock_after = any(docks_config.get(f"{side_str}-{i}-{k}", "none") == "dock" for k in range(slots_per_bay))
                    dock_before = any(docks_config.get(f"{side_str}-{i-1}-{k}", "none") == "dock" for k in range(slots_per_bay))
                    if dock_after or dock_before:
                        depth = params.dock_foundation_depth

                column_base_y = -depth
                column_height = column_top_y - column_base_y

                columns.append(Component3D(
                    type="column", position=[x_pos, column_base_y + (column_height / 2), z_pos],
                    rotation=[0, 0, 0], scale=[section[0], column_height, section[1]]
                ))

        # 2. SŁUPY SZCZYTOWE
        gable_xs = []
        curr_x = -half_width + 6.0
        while curr_x < half_width - 0.1:
            # POMIJAMY OSIĘ SŁUPÓW WEWNĘTRZNYCH RAMY (żeby nie dublować słupa na szczycie w osi nawy)
            if params.number_of_aisles > 1:
                 aisle_width = params.width / params.number_of_aisles
                 is_on_axis = any(abs(curr_x - (-half_width + j * aisle_width)) < 0.1 for j in range(1, params.number_of_aisles))
                 if not is_on_axis:
                     gable_xs.append(curr_x)
            else:
                 gable_xs.append(curr_x)
            curr_x += 6.0

        for z_pos in [-params.length / 2, params.length / 2]:
            for x_pos in gable_xs:
                angle_rad = math.radians(params.roof_angle) if params.roof_drainage_type == "gravity" else 0
                h_roof = params.clear_height + params.truss_depth + (half_width - abs(x_pos)) * math.tan(angle_rad)
                
                column_base_y = -params.foundation_depth
                column_height = h_roof - column_base_y
                
                columns.append(Component3D(
                    type="column_gable", position=[x_pos, column_base_y + (column_height / 2), z_pos],
                    rotation=[0, 0, 0], scale=[sec_int_clad[0], column_height, sec_int_clad[1]]
                ))

        # 3. SŁUPY POŚREDNIE WZDŁUŻNE
        if params.bay_spacing >= 8.0:
            for i in range(num_frames - 1):
                z_mid = (i * params.bay_spacing) + (params.bay_spacing / 2) - (params.length / 2)
                
                for side_str, x_pos in [("left", -half_width), ("right", half_width)]:
                    # Szukamy czy obok jest dok, zeby obniżyć rzędną Y posadowienia
                    is_dock = any(docks_config.get(f"{side_str}-{i}-{k}", "none") == "dock" for k in range(slots_per_bay))
                    depth = params.dock_foundation_depth if is_dock else params.foundation_depth
                    
                    column_base_y = -depth
                    
                    angle_rad = math.radians(params.roof_angle) if params.roof_drainage_type == "gravity" else 0
                    h_roof = params.clear_height + params.truss_depth + (half_width - abs(x_pos)) * math.tan(angle_rad)
                    column_height = h_roof - column_base_y
                    
                    columns.append(Component3D(
                        type="column_gable", position=[x_pos, column_base_y + (column_height / 2), z_mid],
                        rotation=[0, 0, 0], scale=[sec_int_clad[0], column_height, sec_int_clad[1]]
                    ))

        return columns