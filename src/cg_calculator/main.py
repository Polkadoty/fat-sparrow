import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from cg_model import CGModel, Component
from model_importer import ModelImporter
from visualization import CGVisualizer
import json
import csv
from typing import List, Tuple, Dict, Optional

def load_components_from_csv(filename: str) -> List[Component]:
    """Load components from a CSV file"""
    components = []
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse location and size
            location = tuple(float(x) for x in row['location'].strip('()').split(','))
            
            # Size is optional
            size = (0.1, 0.1, 0.1)  # Default size
            if 'size' in row and row['size']:
                size = tuple(float(x) for x in row['size'].strip('()').split(','))
            
            # Create component
            component = Component(
                name=row['name'],
                weight=float(row['weight']),
                location=location,
                size=size,
                color=row.get('color', "#1f77b4"),
                category=row.get('category', "structure"),
                is_consumable=row.get('is_consumable', "False").lower() == "true",
                consumption_rate=float(row.get('consumption_rate', 0.0))
            )
            components.append(component)
    
    return components

def create_sample_csv(filename: str) -> None:
    """Create a sample CSV file with component data"""
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow([
            'name', 'weight', 'location', 'size', 'color', 'category', 
            'is_consumable', 'consumption_rate'
        ])
        writer.writerow([
            'Fuselage', '500', '(0,0,0)', '(4,0.5,0.5)', '#1f77b4', 'structure', 
            'False', '0'
        ])
        writer.writerow([
            'Left Wing', '150', '(0,1,0)', '(1.5,2,0.1)', '#1f77b4', 'structure', 
            'False', '0'
        ])
        writer.writerow([
            'Right Wing', '150', '(0,-1,0)', '(1.5,2,0.1)', '#1f77b4', 'structure', 
            'False', '0'
        ])
        writer.writerow([
            'Engine', '200', '(-1.5,0,0)', '(0.8,0.5,0.5)', '#d62728', 'equipment', 
            'False', '0'
        ])
        writer.writerow([
            'Fuel Tank', '100', '(0.5,0,0)', '(0.5,0.5,0.5)', '#2ca02c', 'fuel', 
            'True', '20'
        ])
        writer.writerow([
            'Pilot', '80', '(1,0,0)', '(0.4,0.4,1)', '#9467bd', 'crew', 
            'False', '0'
        ])
        writer.writerow([
            'Payload', '120', '(-0.5,0,0)', '(0.6,0.6,0.6)', '#ff7f0e', 'payload', 
            'False', '0'
        ])

def main():
    parser = argparse.ArgumentParser(description='Aircraft Center of Gravity Calculator')
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create new model command
    create_parser = subparsers.add_parser('create', help='Create a new CG model')
    create_parser.add_argument('--name', type=str, default='Aircraft', help='Aircraft name')
    create_parser.add_argument('--components', type=str, help='CSV file with component data')
    create_parser.add_argument('--model', type=str, help='3D model file (STL, OBJ, etc.)')
    create_parser.add_argument('--output', type=str, default='outputs/cg_calculator/model.json', 
                              help='Output file for the model')
    
    # Load existing model command
    load_parser = subparsers.add_parser('load', help='Load an existing CG model')
    load_parser.add_argument('--model', type=str, required=True, help='JSON model file to load')
    load_parser.add_argument('--components', type=str, help='CSV file with additional components')
    load_parser.add_argument('--3d-model', type=str, dest='model_3d', help='3D model file (STL, OBJ, etc.)')
    
    # Visualize command
    vis_parser = subparsers.add_parser('visualize', help='Visualize CG model')
    vis_parser.add_argument('--model', type=str, required=True, help='JSON model file to visualize')
    vis_parser.add_argument('--output', type=str, default='outputs/cg_calculator/cg_visualization.png',
                           help='Output file for visualization')
    vis_parser.add_argument('--animate', action='store_true', help='Create animation of CG shift during consumption')
    vis_parser.add_argument('--time', type=float, default=5.0, help='Maximum time for consumption animation (hours)')
    
    # Sample command
    sample_parser = subparsers.add_parser('sample', help='Create sample files')
    sample_parser.add_argument('--output', type=str, default='outputs/cg_calculator/sample_components.csv',
                              help='Output file for sample CSV')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs('outputs/cg_calculator', exist_ok=True)
    
    # Handle commands
    if args.command == 'create':
        # Create new model
        model = CGModel(aircraft_name=args.name)
        
        # Load components if provided
        if args.components:
            components = load_components_from_csv(args.components)
            for comp in components:
                model.add_component(comp)
        
        # Load 3D model if provided
        if args.model:
            model.model_path = args.model
        
        # Save model
        model.save_to_file(args.output)
        print(f"Created new CG model with {len(model.components)} components")
        print(f"Model saved to {args.output}")
        
        # Calculate and display CG
        cg = model.calculate_cg()
        print(f"Center of Gravity: ({cg[0]:.2f}, {cg[1]:.2f}, {cg[2]:.2f})")
        print(f"Total Weight: {model.get_total_weight():.2f}")
        
    elif args.command == 'load':
        # Load existing model
        model = CGModel.load_from_file(args.model)
        print(f"Loaded CG model '{model.aircraft_name}' with {len(model.components)} components")
        
        # Load additional components if provided
        if args.components:
            new_components = load_components_from_csv(args.components)
            for comp in new_components:
                model.add_component(comp)
            print(f"Added {len(new_components)} components from {args.components}")
            
            # Save updated model
            model.save_to_file(args.model)
            print(f"Updated model saved to {args.model}")
        
        # Update 3D model if provided
        if args.model_3d:
            model.model_path = args.model_3d
            model.save_to_file(args.model)
            print(f"Updated 3D model path to {args.model_3d}")
        
        # Calculate and display CG
        cg = model.calculate_cg()
        print(f"Center of Gravity: ({cg[0]:.2f}, {cg[1]:.2f}, {cg[2]:.2f})")
        print(f"Total Weight: {model.get_total_weight():.2f}")
        
    elif args.command == 'visualize':
        # Load model
        model = CGModel.load_from_file(args.model)
        print(f"Loaded CG model '{model.aircraft_name}' with {len(model.components)} components")
        
        # Create visualizer
        visualizer = CGVisualizer(model)
        
        # Load 3D model if available
        if model.model_path and os.path.exists(model.model_path):
            mesh = ModelImporter.import_model(model.model_path)
            if mesh:
                visualizer.set_mesh(mesh)
                print(f"Loaded 3D model from {model.model_path}")
            else:
                print(f"Failed to load 3D model from {model.model_path}")
        
        # Create visualization
        if args.animate:
            # Create animation of CG shift during consumption
            output_file = args.output.replace('.png', '.gif')
            visualizer.save_consumption_animation(output_file, max_time=args.time)
            print(f"Created CG shift animation: {output_file}")
        else:
            # Create static visualization
            visualizer.save_static_visualization(args.output)
            print(f"Created CG visualization: {args.output}")
        
        # Display CG information
        cg = model.calculate_cg()
        print(f"Center of Gravity: ({cg[0]:.2f}, {cg[1]:.2f}, {cg[2]:.2f})")
        print(f"Total Weight: {model.get_total_weight():.2f}")
        
    elif args.command == 'sample':
        # Create sample CSV
        create_sample_csv(args.output)
        print(f"Created sample component CSV at {args.output}")
        
        # Create a sample model
        model = CGModel(aircraft_name="Sample Aircraft")
        components = load_components_from_csv(args.output)
        for comp in components:
            model.add_component(comp)
        
        # Save sample model
        model_output = os.path.join(os.path.dirname(args.output), 'sample_model.json')
        model.save_to_file(model_output)
        print(f"Created sample model at {model_output}")
        
        # Create visualization
        visualizer = CGVisualizer(model)
        vis_output = os.path.join(os.path.dirname(args.output), 'sample_visualization.png')
        visualizer.save_static_visualization(vis_output)
        print(f"Created sample visualization at {vis_output}")
        
    else:
        # No command specified, show help
        parser.print_help()

if __name__ == "__main__":
    main() 