"""
Core module — fundamenty architektury Node Graph.
Zawiera klasy bazowe, system siatki, silnik PPOŻ i detektor kolizji.
"""

from .building_element import BuildingElement, ElementCategory, ElementPriority, FireRating
from .defaults import DEFAULTS
from .grid_system import GridSystem3D, GridNode
from .fire_safety import FireSafetyManager, FireClassification, FireRequirements
from .clash_detector import ClashDetector, Clash, ValidationResult

__all__ = [
    "BuildingElement",
    "ElementCategory",
    "ElementPriority",
    "FireRating",
    "DEFAULTS",
    "GridSystem3D",
    "GridNode",
    "FireSafetyManager",
    "FireClassification",
    "FireRequirements",
    "ClashDetector",
    "Clash",
    "ValidationResult",
]
