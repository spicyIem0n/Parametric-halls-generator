from models import Component3D, HallParameters

class DockFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        elements = []
        num_frames = int(params.length // params.bay_spacing) + 1
        
        # Obliczenie lica zewnętrznego obudowy (Oś + Słup + Grubość płyty)
        col_w = 0.5
        wall_t = params.cladding_thickness
        half_w = params.width / 2
        
        # Zabezpieczenie przed pustym słownikiem
        docks_config = params.docks_config if params.docks_config else {}
        
        # Współrzędne X zewnętrznego lica płyty (tam doklejamy fartuch)
        left_x = -half_w - col_w/2 - wall_t/2
        right_x = half_w + col_w/2 + wall_t/2

        # Podział przęsła na sloty (np. dla przęsła 12m -> 3 sloty)
        slots_per_bay = max(1, int(params.bay_spacing // 4.0))
        slot_w = params.bay_spacing / slots_per_bay

        for i in range(num_frames - 1):
            bay_z_start = (i * params.bay_spacing) - (params.length / 2)
            
            for k in range(slots_per_bay):
                # Zamiast brać środek całego przęsła, bierzemy środek małego slotu
                z_center = bay_z_start + (k * slot_w) + (slot_w / 2)
                
                # --- LEWA ŚCIANA (-1 dla kierunku "na zewnątrz") ---
                left_type = docks_config.get(f"left-{i}-{k}", "none")
                if left_type == "dock":
                    elements.extend(DockFactory._build_dock(left_x, z_center, -1))
                elif left_type == "gate":
                    elements.extend(DockFactory._build_gate(left_x, z_center, -1))

                # --- PRAWA ŚCIANA (+1 dla kierunku "na zewnątrz") ---
                right_type = docks_config.get(f"right-{i}-{k}", "none")
                if right_type == "dock":
                    elements.extend(DockFactory._build_dock(right_x, z_center, 1))
                elif right_type == "gate":
                    elements.extend(DockFactory._build_gate(right_x, z_center, 1))
                
        return elements

    @staticmethod
    def _build_dock(x, z, direction):
        """Generuje model doku opuszczonego na poziom 0 z fartuchem uszczelniającym"""
        elements = []
        # TĄ ZMIENNĄ WŁAŚNIE WYSTREBOWAŁEM DO ZERA
        dock_h = 0.0 
        
        door_w = 3.0  # Szerokość bramy
        door_h = 3.0  # Wysokość bramy
        
        # Brama (opuszczona)
        elements.append(Component3D(type="dock_door", position=[x, dock_h + door_h/2, z], rotation=[0,0,0], scale=[0.1, door_h, door_w]))
        
        # Fartuch uszczelniający (wysuwa się poza lico zgodnie z 'direction')
        shelter_depth = 0.6
        shelter_x = x + (direction * shelter_depth / 2)
        
        # Górna belka fartucha
        elements.append(Component3D(type="dock_shelter", position=[shelter_x, dock_h + door_h + 0.15, z], rotation=[0,0,0], scale=[shelter_depth, 0.3, door_w + 0.6]))
        # Boczne piony fartucha
        elements.append(Component3D(type="dock_shelter", position=[shelter_x, dock_h + door_h/2, z - door_w/2 - 0.15], rotation=[0,0,0], scale=[shelter_depth, door_h, 0.3]))
        elements.append(Component3D(type="dock_shelter", position=[shelter_x, dock_h + door_h/2, z + door_w/2 + 0.15], rotation=[0,0,0], scale=[shelter_depth, door_h, 0.3]))
        
        return elements

    @staticmethod
    def _build_gate(x, z, direction):
        """Generuje bramę kurierską z poziomu 0.00"""
        elements = []
        door_w = 4.0
        door_h = 4.0
        
        # Brama "siada" bezpośrednio na płycie posadzkowej (Y = door_h / 2)
        elements.append(Component3D(type="gate_door", position=[x, door_h/2, z], rotation=[0,0,0], scale=[0.1, door_h, door_w]))
        
        return elements