from models import Component3D, HallParameters

class FoundationFactory:
    DEFAULT_SIZES = {
        "external_main": [2.0, 2.0, 0.5],
        "internal_main": [1.5, 1.5, 0.5],
        "intermediate_cladding": [1.2, 1.2, 0.5],
        "external_dock": [2.5, 3.5, 0.6],
        "internal_dock": [2.0, 2.5, 0.6]
    }

    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        elements = []
        num_frames = int(params.length // params.bay_spacing) + 1
        half_width = params.width / 2

        manual_sizes = params.manual_sizes if params.manual_sizes else {}
        docks_config = params.docks_config if params.docks_config else {}
        slots_per_bay = max(1, int(params.bay_spacing // 4.0))

        # Zabezpieczenie przed błędem, gdy foundation_method nie jest ustawione poprawnie
        size_ext = manual_sizes.get("external_main", FoundationFactory.DEFAULT_SIZES["external_main"]) if params.foundation_method == "manual" else FoundationFactory.DEFAULT_SIZES["external_main"]
        size_int_main = manual_sizes.get("internal_main", FoundationFactory.DEFAULT_SIZES["internal_main"]) if params.foundation_method == "manual" else FoundationFactory.DEFAULT_SIZES["internal_main"]
        size_int_clad = manual_sizes.get("intermediate_cladding", FoundationFactory.DEFAULT_SIZES["intermediate_cladding"]) if params.foundation_method == "manual" else FoundationFactory.DEFAULT_SIZES["intermediate_cladding"]


        # 1. STOPY POD RAMY GŁÓWNE
        for i in range(num_frames):
            z_pos = i * params.bay_spacing - (params.length / 2)
            
            xs = [-half_width]
            if params.number_of_aisles > 1:
                aisle_width = params.width / params.number_of_aisles
                for j in range(1, params.number_of_aisles):
                    xs.append(-half_width + j * aisle_width)
            xs.append(half_width)
            
            for x_pos in xs:
                is_ext = (x_pos == -half_width or x_pos == half_width)
                size = size_ext if is_ext else size_int_main
                
                side_str = "left" if x_pos == -half_width else ("right" if x_pos == half_width else None)
                depth = params.foundation_depth
                
                if side_str:
                    dock_after = any(docks_config.get(f"{side_str}-{i}-{k}", "none") == "dock" for k in range(slots_per_bay))
                    dock_before = any(docks_config.get(f"{side_str}-{i-1}-{k}", "none") == "dock" for k in range(slots_per_bay))
                    if dock_after or dock_before:
                        depth = params.dock_foundation_depth
                
                y_pos = -depth + (size[2] / 2)
                
                elements.append(Component3D(
                    type="foundation", position=[x_pos, y_pos, z_pos], rotation=[0, 0, 0], scale=[size[0], size[2], size[1]]
                ))

        # 2. STOPY SZCZYTOWE
        gable_xs = []
        curr_x = -half_width + 6.0
        while curr_x < half_width - 0.1:
            if params.number_of_aisles > 1:
                 aisle_width = params.width / params.number_of_aisles
                 is_on_axis = any(abs(curr_x - (-half_width + j * aisle_width)) < 0.1 for j in range(1, params.number_of_aisles))
                 if not is_on_axis: gable_xs.append(curr_x)
            else:
                 gable_xs.append(curr_x)
            curr_x += 6.0

        for z_pos in [-params.length / 2, params.length / 2]:
            for x_pos in gable_xs:
                y_pos = -params.foundation_depth + (size_int_clad[2] / 2)
                elements.append(Component3D(
                    type="foundation", position=[x_pos, y_pos, z_pos], rotation=[0, 0, 0], scale=[size_int_clad[0], size_int_clad[2], size_int_clad[1]]
                ))

        # 3. STOPY POŚREDNIE WZDŁUŻNE
        if params.bay_spacing >= 8.0:
            for i in range(num_frames - 1):
                z_mid = (i * params.bay_spacing) + (params.bay_spacing / 2) - (params.length / 2)
                for side_str, x_pos in [("left", -half_width), ("right", half_width)]:
                    # POPRAWKA 3: Jesli w calym przesle na danej ścianie jest jakikolwiek dok to opuszczamy stopę pośrednią
                    is_dock = any(docks_config.get(f"{side_str}-{i}-{k}", "none") == "dock" for k in range(slots_per_bay))
                    depth = params.dock_foundation_depth if is_dock else params.foundation_depth
                    
                    y_pos = -depth + (size_int_clad[2] / 2)
                    
                    elements.append(Component3D(
                        type="foundation", position=[x_pos, y_pos, z_mid], rotation=[0, 0, 0], scale=[size_int_clad[0], size_int_clad[2], size_int_clad[1]]
                    ))

        return elements