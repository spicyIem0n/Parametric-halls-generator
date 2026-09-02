"""
IfcExporter — eksport wygenerowanego modelu 3D hali do formatu IFC (IFC4).

Faza 1 (masing / koordynacja — LOD 200-300):
- Każdy Component3D (box: position/rotation/scale) zapisywany jest jako
  bryła IfcExtrudedAreaSolid z prostokątnym profilem, umieszczona we
  właściwym IfcLocalPlacement.
- Elementy grupowane są w jedną kondygnację (IfcBuildingStorey) w ramach
  standardowej hierarchii IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey.
- element_type mapowany jest na najbliższą klasę IFC (patrz ELEMENT_TYPE_TO_IFC_CLASS).
- Metadane (meta: fire_rating, category, block_id) zapisywane są jako
  IfcPropertySet "Pset_HaleParametryczne_Meta" na każdym elemencie.

Ograniczenia świadomie przyjęte w Fazie 1:
- Słupy/rygle/płatwie eksportowane są jako prostokątne bryły, nie jako
  rzeczywiste przekroje stalowe (IPE/HEA) — do rozbudowy w kolejnej fazie.
- Cały model trafia na jedną kondygnację ("Poziom 0") niezależnie od
  antresol/biur — rozbicie na realne IfcBuildingStorey to Faza 2/3.

Układ współrzędnych:
- Backend/frontend (three.js) używają konwencji Y-up, prawoskrętnej.
- IFC/STEP wymaga Z-up, prawoskrętnej.
- Zamiana zachowująca skrętność: ifc(x, y, z) = threejs(x, -z, y).
- Rotacje to kąty Eulera (rx, ry, rz) w radianach, w konwencji Three.js
  'XYZ' (macierz R = Rx * Ry * Rz aplikowana na wektor lokalny) — dokładnie
  ta sama konwencja co w generators/hall_generator.py (_euler_xyz_to_matrix).
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Tuple

import ifcopenshell
import ifcopenshell.guid as ifc_guid

from models import Component3D, HallParameters


# --- Mapowanie typu elementu (Component3D.type) na klasę IFC ---
# Wartość: (klasa_IFC, PredefinedType | None)
ELEMENT_TYPE_TO_IFC_CLASS: Dict[str, Tuple[str, Optional[str]]] = {
    # Konstrukcja nośna
    "column": ("IfcColumn", None),
    "column_gable": ("IfcColumn", None),
    "office_column": ("IfcColumn", None),
    "mezzanine_column": ("IfcColumn", None),
    "girt": ("IfcBeam", None),
    "purlin_strut": ("IfcBeam", None),
    "trimmer": ("IfcBeam", None),
    "bracing": ("IfcMember", "BRACE"),
    "bracing_roof": ("IfcMember", "BRACE"),
    "reserve_purlin_doubled": ("IfcBeam", None),
    "reserve_truss_marker": ("IfcBuildingElementProxy", None),
    "reserve_zone_marker": ("IfcBuildingElementProxy", None),

    # Fundamenty
    "foundation": ("IfcFooting", "PAD_FOOTING"),
    "plinth": ("IfcFooting", "STRIP_FOOTING"),

    # Płyty / posadzki
    "floor_slab": ("IfcSlab", "FLOOR"),
    "office_slab": ("IfcSlab", "FLOOR"),
    "tech_room_slab": ("IfcSlab", "FLOOR"),
    "mezzanine_slab": ("IfcSlab", "FLOOR"),

    # Ściany / obudowa
    "sandwich_panel": ("IfcWall", None),
    "fire_wall": ("IfcWall", "FIRE_PARTITIONING"),
    "mezzanine_fire_wall": ("IfcWall", "FIRE_PARTITIONING"),
    "office_fire_wall": ("IfcWall", "FIRE_PARTITIONING"),
    "office_wall": ("IfcWall", None),
    "tech_room_wall": ("IfcWall", None),
    "cladding_rail": ("IfcMember", None),

    # Dach
    "roof_panel": ("IfcRoof", None),
    "office_roof": ("IfcRoof", None),
    "fire_strip_roof": ("IfcCovering", "ROOFING"),
    "drainage_inlet": ("IfcFlowFitting", None),

    # Otwory / stolarka
    "dock_door": ("IfcDoor", None),
    "gate_door": ("IfcDoor", None),
    "tech_room_door": ("IfcDoor", None),
    "light_strip": ("IfcWindow", None),
    "smoke_vent": ("IfcWindow", None),
    "dock_shelter": ("IfcBuildingElementProxy", None),

    # Komunikacja / wyposażenie
    "office_stairs": ("IfcStair", None),
    "mezzanine_stairs": ("IfcStair", None),
    "mezzanine_balustrade": ("IfcRailing", None),
}

DEFAULT_IFC_CLASS = ("IfcBuildingElementProxy", None)

MIN_DIM = 0.001  # [m] — minimalny wymiar bryły, zabezpieczenie przed geometrią zdegenerowaną


# --- Pomocnicze operacje macierzowe (spójne z hall_generator._euler_xyz_to_matrix) ---

def _mat_mult(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _rot_x(t):
    c, s = math.cos(t), math.sin(t)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def _rot_y(t):
    c, s = math.cos(t), math.sin(t)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def _rot_z(t):
    c, s = math.cos(t), math.sin(t)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def _euler_xyz_to_matrix(rx, ry, rz):
    """R = Rx * Ry * Rz — identyczna konwencja jak we frontendzie (Three.js 'XYZ')."""
    return _mat_mult(_mat_mult(_rot_x(rx), _rot_y(ry)), _rot_z(rz))


def _mat_vec(r, v):
    return (
        r[0][0] * v[0] + r[0][1] * v[1] + r[0][2] * v[2],
        r[1][0] * v[0] + r[1][1] * v[1] + r[1][2] * v[2],
        r[2][0] * v[0] + r[2][1] * v[1] + r[2][2] * v[2],
    )


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _to_ifc_space(v):
    """Zamiana Three.js Y-up -> IFC Z-up, z zachowaniem skrętności układu."""
    x, y, z = v
    return (x, -z, y)


class IfcExportBuilder:
    """Buduje plik IFC4 na podstawie listy Component3D wygenerowanej przez HallGenerator."""

    def __init__(self, params: HallParameters):
        self.params = params
        self.file = ifcopenshell.file(schema="IFC4")
        self._owner_history = None
        self._context = None
        self._sub_context_body = None
        self._storey = None

    # -- API publiczne --

    def build(self, components: List[Component3D]) -> ifcopenshell.file:
        self._setup_header_and_units()
        self._setup_spatial_structure()
        for comp in components:
            self._add_element(comp)
        return self.file

    # -- Budowa szkieletu projektu --

    def _guid(self) -> str:
        return ifc_guid.new()

    def _setup_header_and_units(self):
        f = self.file

        length_unit = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
        area_unit = f.create_entity("IfcSIUnit", UnitType="AREAUNIT", Name="SQUARE_METRE")
        volume_unit = f.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT", Name="CUBIC_METRE")
        angle_unit = f.create_entity("IfcSIUnit", UnitType="PLANEANGLEUNIT", Name="RADIAN")
        unit_assignment = f.create_entity(
            "IfcUnitAssignment", Units=[length_unit, area_unit, volume_unit, angle_unit]
        )

        origin = f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        world_z = f.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
        world_x = f.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))
        world_placement = f.create_entity(
            "IfcAxis2Placement3D", Location=origin, Axis=world_z, RefDirection=world_x
        )

        self._context = f.create_entity(
            "IfcGeometricRepresentationContext",
            ContextType="Model",
            CoordinateSpaceDimension=3,
            Precision=1.0e-5,
            WorldCoordinateSystem=world_placement,
            TrueNorth=None,
        )
        self._sub_context_body = f.create_entity(
            "IfcGeometricRepresentationSubContext",
            ContextIdentifier="Body",
            ContextType="Model",
            ParentContext=self._context,
            TargetView="MODEL_VIEW",
        )

        width = getattr(self.params, "width", 0) or 0
        length = getattr(self.params, "length", 0) or 0
        project_name = f"Hala parametryczna {width:.0f}x{length:.0f} m" if width and length else "Hala parametryczna"

        self._project = f.create_entity(
            "IfcProject",
            GlobalId=self._guid(),
            Name=project_name,
            UnitsInContext=unit_assignment,
            RepresentationContexts=[self._context],
        )

    def _local_placement(self, relative_to=None):
        f = self.file
        origin = f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        axis2 = f.create_entity("IfcAxis2Placement3D", Location=origin, Axis=None, RefDirection=None)
        return f.create_entity("IfcLocalPlacement", PlacementRelTo=relative_to, RelativePlacement=axis2)

    def _setup_spatial_structure(self):
        f = self.file

        site = f.create_entity(
            "IfcSite",
            GlobalId=self._guid(),
            Name="Działka",
            ObjectPlacement=self._local_placement(),
            CompositionType="ELEMENT",
        )
        building = f.create_entity(
            "IfcBuilding",
            GlobalId=self._guid(),
            Name="Hala",
            ObjectPlacement=self._local_placement(site.ObjectPlacement),
            CompositionType="ELEMENT",
        )
        storey = f.create_entity(
            "IfcBuildingStorey",
            GlobalId=self._guid(),
            Name="Poziom 0",
            ObjectPlacement=self._local_placement(building.ObjectPlacement),
            CompositionType="ELEMENT",
            Elevation=0.0,
        )

        f.create_entity(
            "IfcRelAggregates",
            GlobalId=self._guid(),
            RelatingObject=self._project,
            RelatedObjects=[site],
        )
        f.create_entity(
            "IfcRelAggregates",
            GlobalId=self._guid(),
            RelatingObject=site,
            RelatedObjects=[building],
        )
        f.create_entity(
            "IfcRelAggregates",
            GlobalId=self._guid(),
            RelatingObject=building,
            RelatedObjects=[storey],
        )

        self._storey = storey
        self._storey_elements: List = []

    # -- Elementy --

    def _add_element(self, comp: Component3D):
        f = self.file

        sx, sy, sz = comp.scale
        sx, sy, sz = max(abs(sx), MIN_DIM), max(abs(sy), MIN_DIM), max(abs(sz), MIN_DIM)
        cx, cy, cz = comp.position
        rx, ry, rz = comp.rotation

        rot = _euler_xyz_to_matrix(rx, ry, rz)

        # Dolna krawędź bryły w lokalnym układzie (box wyśrodkowany na position) — punkt startowy wyciągnięcia.
        world_bottom = _add(_mat_vec(rot, (0.0, -sy / 2.0, 0.0)), (cx, cy, cz))
        axis_dir = _mat_vec(rot, (0.0, 1.0, 0.0))     # lokalna "góra" -> kierunek wyciągnięcia
        ref_dir = _mat_vec(rot, (1.0, 0.0, 0.0))      # lokalna "szerokość" -> kierunek osi X profilu

        location_ifc = _to_ifc_space(world_bottom)
        axis_ifc = _to_ifc_space(axis_dir)
        ref_ifc = _to_ifc_space(ref_dir)

        placement3d = f.create_entity(
            "IfcAxis2Placement3D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=location_ifc),
            Axis=f.create_entity("IfcDirection", DirectionRatios=axis_ifc),
            RefDirection=f.create_entity("IfcDirection", DirectionRatios=ref_ifc),
        )
        object_placement = f.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=self._storey.ObjectPlacement,
            RelativePlacement=placement3d,
        )

        # Profil prostokątny w płaszczyźnie lokalnej XY (X=szerokość sx, Y=głębokość sz), wyciągnięty o wysokość sy.
        profile_placement = f.create_entity(
            "IfcAxis2Placement2D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0)),
        )
        profile = f.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            Position=profile_placement,
            XDim=sx,
            YDim=sz,
        )
        extrude_dir = f.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
        solid = f.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=f.create_entity(
                "IfcAxis2Placement3D",
                Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
            ),
            ExtrudedDirection=extrude_dir,
            Depth=sy,
        )
        shape_rep = f.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=self._sub_context_body,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[solid],
        )
        product_shape = f.create_entity("IfcProductDefinitionShape", Representations=[shape_rep])

        ifc_class, predefined_type = ELEMENT_TYPE_TO_IFC_CLASS.get(comp.type, DEFAULT_IFC_CLASS)
        entity_name = (comp.meta or {}).get("name") or comp.type

        kwargs = dict(
            GlobalId=self._guid(),
            Name=entity_name,
            ObjectPlacement=object_placement,
            Representation=product_shape,
        )
        if predefined_type is not None:
            kwargs["PredefinedType"] = predefined_type

        try:
            element = f.create_entity(ifc_class, **kwargs)
        except Exception:
            # Klasa nie obsluguje PredefinedType albo nie istnieje w schemacie — fallback bezpieczny.
            kwargs.pop("PredefinedType", None)
            try:
                element = f.create_entity(ifc_class, **kwargs)
            except Exception:
                element = f.create_entity("IfcBuildingElementProxy", **kwargs)

        self._storey_elements.append(element)

        if comp.meta:
            self._add_property_set(element, comp.meta)

    def _add_property_set(self, element, meta: Dict[str, str]):
        f = self.file
        properties = [
            f.create_entity(
                "IfcPropertySingleValue",
                Name=str(key),
                NominalValue=f.createIfcLabel(str(value)),
            )
            for key, value in meta.items()
        ]
        if not properties:
            return
        pset = f.create_entity(
            "IfcPropertySet",
            GlobalId=self._guid(),
            Name="Pset_HaleParametryczne_Meta",
            HasProperties=properties,
        )
        f.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=self._guid(),
            RelatedObjects=[element],
            RelatingPropertyDefinition=pset,
        )

    def finalize_containment(self):
        """Dopina wszystkie utworzone elementy do IfcBuildingStorey jednym IfcRelContainedInSpatialStructure."""
        if not self._storey_elements:
            return
        self.file.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=self._guid(),
            RelatingStructure=self._storey,
            RelatedElements=self._storey_elements,
        )


def build_ifc_file(params: HallParameters, components: Iterable[Component3D]) -> ifcopenshell.file:
    """Punkt wejścia: buduje kompletny plik IFC z parametrów hali i wygenerowanej geometrii."""
    builder = IfcExportBuilder(params)
    builder.build(list(components))
    builder.finalize_containment()
    return builder.file


def export_ifc_to_bytes(params: HallParameters, components: Iterable[Component3D]) -> bytes:
    ifc_file = build_ifc_file(params, components)
    return ifc_file.to_string().encode("utf-8")
