from models import Component3D, HallParameters

class FoundationFactory:
    DEFAULT_SIZES = {
        "external_main": [2.5, 4.0, 0.45], "internal_main": [2.5, 2.5, 0.45],
        "intermediate_cladding": [1.5, 1.5, 0.40], "external_dock": [2.7, 3.5, 0.45], "internal_dock": [2.5, 3.7, 0.45]
    }

    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        footings = []
        num_frames = int(params.length // params.bay_spacing) + 1
        
        for i in range(num_frames):
            z_pos = i * params.bay_spacing - (params.length / 2)
            
            for j in range(params.number_of_aisles + 1):
                x_pos = -params.width / 2 + j * (params.width / params.number_of_aisles)
                
                # Ustalenie czy to nawa skrajna (zewnętrzna)
                is_left_ext = (j == 0)
                is_right_ext = (j == params.number_of_aisles)
                is_external = is_left_ext or is_right_ext
                
                # Sprawdzenie strefy dokowej dla danej ściany
                is_dock_here = (is_left_ext and params.left_dock_zone) or (is_right_ext and params.right_dock_zone)
                
                if is_external:
                    f_type = "external_dock" if is_dock_here else "external_main"
                else:
                    f_type = "internal_dock" if is_dock_here else "internal_main" # MVP: jeśli hala ma dok z lewej, wew. słupy mogą dziedziczyć głębokość
                
                if params.foundation_method == "manual":
                    size = params.manual_sizes.get(f_type, FoundationFactory.DEFAULT_SIZES[f_type])
                else:
                    size = FoundationFactory.DEFAULT_SIZES[f_type]
                
                dim_x, dim_y, dim_z = size[1], size[2], size[0]
                depth = params.dock_foundation_depth if is_dock_here else params.foundation_depth
                
                # Rzędna Y: Dno stopy to -depth. Wierzch to -depth + dim_y. Środek to -depth + (dim_y / 2)
                y_pos = -depth + (dim_y / 2)
                
                footings.append(Component3D(
                    type="foundation", position=[x_pos, y_pos, z_pos], rotation=[0, 0, 0], scale=[dim_x, dim_y, dim_z]
                ))
            
        return footings