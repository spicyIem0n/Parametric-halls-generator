from models import Component3D, HallParameters
from .foundation_factory import FoundationFactory

class PlinthFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        elements = []
        num_frames = int(params.length // params.bay_spacing) + 1
        docks_config = params.docks_config if params.docks_config else {}
        slots_per_bay = max(1, int(params.bay_spacing // 4.0))
        slot_w = params.bay_spacing / slots_per_bay
        pt = params.plinth_thickness
        
        found_size_main = params.manual_sizes.get("external_main", FoundationFactory.DEFAULT_SIZES["external_main"]) if params.foundation_method == "manual" else FoundationFactory.DEFAULT_SIZES["external_main"]
        found_h = found_size_main[2]

        # 1. Ściany szczytowe
        found_top_gable = -params.foundation_depth + found_h
        plinth_h_gable = 0.30 - found_top_gable
        for z_pos in [-params.length / 2, params.length / 2]:
            elements.append(Component3D(
                type="plinth", position=[0, found_top_gable + plinth_h_gable/2, z_pos],
                rotation=[0, 0, 0], scale=[params.width, plinth_h_gable, pt]
            ))

        # 2. Ściany boczne (Slot po slocie)
        for i in range(num_frames - 1):
            bay_z_start = (i * params.bay_spacing) - (params.length / 2)
            
            for side in ["left", "right"]:
                x_pos = -params.width / 2 if side == "left" else params.width / 2
                
                for k in range(slots_per_bay):
                    config_val = docks_config.get(f"{side}-{i}-{k}", "none")
                    z_center = bay_z_start + (k * slot_w) + (slot_w / 2)
                    
                    is_dock = (config_val == "dock")
                    depth = params.dock_foundation_depth if is_dock else params.foundation_depth
                    found_top = -depth + found_h
                    
                    if config_val == "none":
                        plinth_h = 0.30 - found_top
                        elements.append(Component3D(type="plinth", position=[x_pos, found_top + plinth_h/2, z_center], rotation=[0,0,0], scale=[pt, plinth_h, slot_w]))
                    else:
                        door_w = 3.0 if config_val == "dock" else 4.0
                        side_w = (slot_w - door_w) / 2
                        plinth_h_side = 0.30 - found_top
                        
                        # Wąsy boczne (do +0.30)
                        if side_w > 0:
                            elements.append(Component3D(type="plinth", position=[x_pos, found_top + plinth_h_side/2, z_center - slot_w/2 + side_w/2], rotation=[0,0,0], scale=[pt, plinth_h_side, side_w]))
                            elements.append(Component3D(type="plinth", position=[x_pos, found_top + plinth_h_side/2, z_center + slot_w/2 - side_w/2], rotation=[0,0,0], scale=[pt, plinth_h_side, side_w]))
                        
                        # Podwalina pod bramą/dokiem (tylko do 0.00)
                        plinth_h_mid = 0.0 - found_top
                        if plinth_h_mid > 0:
                            elements.append(Component3D(type="plinth", position=[x_pos, found_top + plinth_h_mid/2, z_center], rotation=[0,0,0], scale=[pt, plinth_h_mid, door_w]))
                            
        return elements