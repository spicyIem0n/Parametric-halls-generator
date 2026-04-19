import math
from models import Component3D, HallParameters

class CladdingFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        if not params.has_cladding:
            return []
            
        panels = []
        modular_width = 1.1 
        
        col_section = params.manual_column_sections.get("external_main", [0.4, 0.4]) if params.column_method == "manual" else [0.4, 0.4]
        col_x, col_z = col_section[0], col_section[1]
        t = params.cladding_thickness
        
        left_x = -params.width / 2 - (col_x / 2) - (t / 2)
        right_x = params.width / 2 + (col_x / 2) + (t / 2)
        front_z = -params.length / 2 - (col_z / 2) - (t / 2)
        back_z = params.length / 2 + (col_z / 2) + (t / 2)
        
        side_span = params.length + col_z + (t * 2)
        gable_span = params.width + col_x + (t * 2)
        
        # Wysokość użyteczna okładziny (od +0.25m do okapu dachu)
        start_y = params.cladding_bottom_level
        net_height = params.clear_height - start_y
        
        if params.cladding_orientation == "horizontal":
            num_panels_y = int(net_height // modular_width) + 1
            for i in range(num_panels_y):
                panel_h = modular_width if (i + 1) * modular_width <= net_height else net_height - (i * modular_width)
                y_pos = start_y + (i * modular_width) + (panel_h / 2)
                
                panels.append(Component3D(type="sandwich_panel", position=[left_x, y_pos, 0], rotation=[0, 0, 0], scale=[t, panel_h, side_span]))
                panels.append(Component3D(type="sandwich_panel", position=[right_x, y_pos, 0], rotation=[0, 0, 0], scale=[t, panel_h, side_span]))
                panels.append(Component3D(type="sandwich_panel", position=[0, y_pos, front_z], rotation=[0, math.pi/2, 0], scale=[t, panel_h, gable_span]))
                panels.append(Component3D(type="sandwich_panel", position=[0, y_pos, back_z], rotation=[0, math.pi/2, 0], scale=[t, panel_h, gable_span]))

        elif params.cladding_orientation == "vertical":
            panels.append(Component3D(type="girt", position=[left_x + t/2, start_y + 0.1, 0], rotation=[0, 0, 0], scale=[0.1, 0.2, side_span]))
            panels.append(Component3D(type="girt", position=[left_x + t/2, params.clear_height, 0], rotation=[0, 0, 0], scale=[0.1, 0.2, side_span]))
            panels.append(Component3D(type="girt", position=[right_x - t/2, start_y + 0.1, 0], rotation=[0, 0, 0], scale=[0.1, 0.2, side_span]))
            panels.append(Component3D(type="girt", position=[right_x - t/2, params.clear_height, 0], rotation=[0, 0, 0], scale=[0.1, 0.2, side_span]))
            
            num_panels_side = int(side_span // modular_width) + 1
            for i in range(num_panels_side):
                panel_w = modular_width if (i + 1) * modular_width <= side_span else side_span - (i * modular_width)
                z_pos = (i * modular_width) + (panel_w / 2) - (side_span / 2)
                y_pos = start_y + (net_height/2)
                
                panels.append(Component3D(type="sandwich_panel_v", position=[left_x, y_pos, z_pos], rotation=[0, 0, 0], scale=[t, net_height, panel_w]))
                panels.append(Component3D(type="sandwich_panel_v", position=[right_x, y_pos, z_pos], rotation=[0, 0, 0], scale=[t, net_height, panel_w]))
            
            num_panels_gable = int(gable_span // modular_width) + 1
            for i in range(num_panels_gable):
                panel_w = modular_width if (i + 1) * modular_width <= gable_span else gable_span - (i * modular_width)
                x_pos = (i * modular_width) + (panel_w / 2) - (gable_span / 2)
                y_pos = start_y + (net_height/2)
                
                panels.append(Component3D(type="sandwich_panel_v", position=[x_pos, y_pos, front_z], rotation=[0, math.pi/2, 0], scale=[t, net_height, panel_w]))
                panels.append(Component3D(type="sandwich_panel_v", position=[x_pos, y_pos, back_z], rotation=[0, math.pi/2, 0], scale=[t, net_height, panel_w]))
                
        return panels