from models import Component3D, HallParameters
from .foundation_factory import FoundationFactory

class PlinthFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        plinths = []
        num_frames = int(params.length // params.bay_spacing) + 1
        
        # Pobranie głębokości fundamentów dla określenia spodu podwaliny
        f_sizes = FoundationFactory.DEFAULT_SIZES if params.foundation_method != "manual" else params.manual_sizes
        
       # Oś podłużna (ściany boczne)
        for i in range(num_frames - 1):
            z_center = (i * params.bay_spacing) + (params.bay_spacing / 2) - (params.length / 2)
            
            # Lewa i prawa strona (obliczenie wysokości z nowej mapy doków)
            for side in ["left", "right"]:
                is_dock = params.docks_config.get(f"{side}-{i}") == "dock"
                f_type = "external_dock" if is_dock else "external_main"
                f_thickness = f_sizes.get(f_type, FoundationFactory.DEFAULT_SIZES["external_main"])[2]
                f_depth = params.dock_foundation_depth if is_dock else params.foundation_depth
                
                plinth_bottom_y = -f_depth + f_thickness
                plinth_height = params.plinth_top_level - plinth_bottom_y
                plinth_y_center = plinth_bottom_y + (plinth_height / 2)
                
                x_pos = -params.width / 2 if side == "left" else params.width / 2
                
                plinths.append(Component3D(
                    type="plinth", position=[x_pos, plinth_y_center, z_center],
                    rotation=[0, 0, 0], scale=[params.plinth_thickness, plinth_height, params.bay_spacing]
                ))
                
        # W MVP dodajemy jeszcze podwaliny szczytowe (przód i tył)
        # Rozpiętość miedzy słupami głównymi (dla uproszczenia jeden długi element)
        front_z = -params.length / 2
        back_z = params.length / 2
        f_thickness = f_sizes.get("external_main", FoundationFactory.DEFAULT_SIZES["external_main"])[2]
        plinth_bottom_y = -params.foundation_depth + f_thickness
        plinth_height = params.plinth_top_level - plinth_bottom_y
        
        plinths.append(Component3D(type="plinth", position=[0, plinth_bottom_y + (plinth_height / 2), front_z], rotation=[0, 1.5708, 0], scale=[params.plinth_thickness, plinth_height, params.width]))
        plinths.append(Component3D(type="plinth", position=[0, plinth_bottom_y + (plinth_height / 2), back_z], rotation=[0, 1.5708, 0], scale=[params.plinth_thickness, plinth_height, params.width]))

        return plinths