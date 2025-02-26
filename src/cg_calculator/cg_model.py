import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import json
import os

@dataclass
class Component:
    """Aircraft component with weight and location information"""
    name: str
    weight: float  # in kg or lbs (consistent units required)
    location: Tuple[float, float, float]  # (x, y, z) coordinates
    size: Tuple[float, float, float] = (0.1, 0.1, 0.1)  # (length, width, height)
    color: str = "#1f77b4"  # Default color
    category: str = "structure"  # Category for grouping (structure, payload, fuel, etc.)
    is_consumable: bool = False  # Whether component is consumable (like fuel)
    consumption_rate: float = 0.0  # Rate of consumption (kg/hr or lbs/hr)
    
    @property
    def moment(self) -> Tuple[float, float, float]:
        """Calculate moment (weight * distance) for each axis"""
        return (
            self.weight * self.location[0],
            self.weight * self.location[1],
            self.weight * self.location[2]
        )


class CGModel:
    """Center of Gravity calculation model for aircraft"""
    
    def __init__(self, aircraft_name: str = "Aircraft"):
        self.aircraft_name = aircraft_name
        self.components: List[Component] = []
        self.reference_point: Tuple[float, float, float] = (0, 0, 0)
        self.model_path: Optional[str] = None
        self.units: str = "metric"  # "metric" or "imperial"
        
    def add_component(self, component: Component) -> None:
        """Add a component to the aircraft"""
        self.components.append(component)
        
    def remove_component(self, component_name: str) -> bool:
        """Remove a component by name"""
        for i, comp in enumerate(self.components):
            if comp.name == component_name:
                self.components.pop(i)
                return True
        return False
    
    def calculate_cg(self) -> Tuple[float, float, float]:
        """Calculate the center of gravity"""
        if not self.components:
            return self.reference_point
            
        total_weight = sum(comp.weight for comp in self.components)
        
        if total_weight == 0:
            return self.reference_point
            
        x_moment = sum(comp.moment[0] for comp in self.components)
        y_moment = sum(comp.moment[1] for comp in self.components)
        z_moment = sum(comp.moment[2] for comp in self.components)
        
        return (
            x_moment / total_weight,
            y_moment / total_weight,
            z_moment / total_weight
        )
    
    def calculate_category_cg(self) -> Dict[str, Tuple[float, float, float]]:
        """Calculate CG for each category of components"""
        categories = {}
        
        # Group components by category
        for comp in self.components:
            if comp.category not in categories:
                categories[comp.category] = []
            categories[comp.category].append(comp)
        
        # Calculate CG for each category
        category_cg = {}
        for category, comps in categories.items():
            total_weight = sum(comp.weight for comp in comps)
            
            if total_weight == 0:
                category_cg[category] = self.reference_point
                continue
                
            x_moment = sum(comp.moment[0] for comp in comps)
            y_moment = sum(comp.moment[1] for comp in comps)
            z_moment = sum(comp.moment[2] for comp in comps)
            
            category_cg[category] = (
                x_moment / total_weight,
                y_moment / total_weight,
                z_moment / total_weight
            )
            
        return category_cg
    
    def get_total_weight(self) -> float:
        """Get the total weight of all components"""
        return sum(comp.weight for comp in self.components)
    
    def simulate_consumption(self, time_hours: float) -> Tuple[float, float, float]:
        """Simulate CG change after consuming resources for given time"""
        # Create a copy of components with adjusted weights for consumables
        adjusted_components = []
        
        for comp in self.components:
            if comp.is_consumable:
                # Calculate remaining weight after consumption
                remaining_weight = max(0, comp.weight - (comp.consumption_rate * time_hours))
                
                # Create adjusted component
                adjusted_comp = Component(
                    name=comp.name,
                    weight=remaining_weight,
                    location=comp.location,
                    size=comp.size,
                    color=comp.color,
                    category=comp.category,
                    is_consumable=comp.is_consumable,
                    consumption_rate=comp.consumption_rate
                )
                adjusted_components.append(adjusted_comp)
            else:
                # Non-consumable components remain unchanged
                adjusted_components.append(comp)
        
        # Calculate CG with adjusted components
        total_weight = sum(comp.weight for comp in adjusted_components)
        
        if total_weight == 0:
            return self.reference_point
            
        x_moment = sum(comp.weight * comp.location[0] for comp in adjusted_components)
        y_moment = sum(comp.weight * comp.location[1] for comp in adjusted_components)
        z_moment = sum(comp.weight * comp.location[2] for comp in adjusted_components)
        
        return (
            x_moment / total_weight,
            y_moment / total_weight,
            z_moment / total_weight
        )
    
    def save_to_file(self, filename: str) -> None:
        """Save the model to a JSON file"""
        # Create directory if it doesn't exist and if there is a directory
        dirname = os.path.dirname(filename)
        if dirname:  # Only try to create directory if there is one
            os.makedirs(dirname, exist_ok=True)
        
        data = {
            "aircraft_name": self.aircraft_name,
            "reference_point": self.reference_point,
            "model_path": self.model_path,
            "units": self.units,
            "components": [
                {
                    "name": comp.name,
                    "weight": comp.weight,
                    "location": comp.location,
                    "size": comp.size,
                    "color": comp.color,
                    "category": comp.category,
                    "is_consumable": comp.is_consumable,
                    "consumption_rate": comp.consumption_rate
                }
                for comp in self.components
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'CGModel':
        """Load a model from a JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        model = cls(aircraft_name=data["aircraft_name"])
        model.reference_point = tuple(data["reference_point"])
        model.model_path = data.get("model_path")
        model.units = data.get("units", "metric")
        
        for comp_data in data["components"]:
            component = Component(
                name=comp_data["name"],
                weight=comp_data["weight"],
                location=tuple(comp_data["location"]),
                size=tuple(comp_data["size"]),
                color=comp_data["color"],
                category=comp_data["category"],
                is_consumable=comp_data.get("is_consumable", False),
                consumption_rate=comp_data.get("consumption_rate", 0.0)
            )
            model.add_component(component)
        
        return model 