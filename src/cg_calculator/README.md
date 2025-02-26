# Center of Gravity Calculator Documentation

The Center of Gravity (CG) Calculator is a tool for aircraft designers and operators to calculate and visualize the center of gravity of an aircraft based on the weight and location of its components.

## Installation Requirements

Before using the CG Calculator, ensure you have the following dependencies installed:

```bash
pip install numpy matplotlib trimesh
```

For 3D model import functionality:
- STL and OBJ files are supported natively
- STEP file import requires FreeCAD to be installed

## Basic Usage

The CG Calculator provides several commands through a command-line interface:

```bash
python src/cg_calculator/main.py <command> [options]
```

Available commands:
- `create`: Create a new CG model
- `load`: Load and modify an existing CG model
- `visualize`: Visualize a CG model
- `sample`: Generate sample files to get started

## Getting Started

The easiest way to get started is to generate sample files:

```bash
python src/cg_calculator/main.py sample
```

This will create:
1. A sample CSV file with component data
2. A sample model JSON file
3. A sample visualization

## Working with Components

### Component CSV Format

Components are defined in a CSV file with the following columns:
- `name`: Component name
- `weight`: Component weight (in consistent units)
- `location`: (x,y,z) coordinates as a tuple string, e.g., "(0,0,0)"
- `size`: (length,width,height) dimensions as a tuple string (optional)
- `color`: HTML color code (optional)
- `category`: Component category (optional)
- `is_consumable`: "True" or "False" (optional)
- `consumption_rate`: Consumption rate for consumable items (optional)

Example CSV row:
```
Fuel Tank,100,"(0.5,0,0)","(0.5,0.5,0.5)","#2ca02c",fuel,True,20
```

### Creating a New Model with Components

```bash
python src/cg_calculator/main.py create --name "My Aircraft" --components components.csv --output my_aircraft.json
```

### Adding Components to an Existing Model

```bash
python src/cg_calculator/main.py load --model my_aircraft.json --components additional_components.csv
```

## Working with 3D Models

### Supported 3D Model Formats

- STL (.stl): Recommended format
- OBJ (.obj): Supported natively
- STEP (.step, .stp): Requires FreeCAD
- Fusion 360 (.f3d): Must be exported to STL first
- OpenVSP (.vsp): Must be exported to STL first

### Adding a 3D Model to a New CG Model

```bash
python src/cg_calculator/main.py create --name "My Aircraft" --components components.csv --model aircraft.stl
```

### Adding a 3D Model to an Existing CG Model

```bash
python src/cg_calculator/main.py load --model my_aircraft.json --3d-model aircraft.stl
```

## Visualization

### Creating a Static Visualization

```bash
python src/cg_calculator/main.py visualize --model my_aircraft.json --output aircraft_cg.png
```

### Creating an Animation of CG Shift During Consumption

This is useful for visualizing how the CG changes as consumable items (like fuel) are used:

```bash
python src/cg_calculator/main.py visualize --model my_aircraft.json --animate --time 5.0
```

The `--time` parameter specifies the maximum time in hours for the animation.

## Complete Workflow Example

1. Create a components CSV file (or use the sample):
   ```bash
   python src/cg_calculator/main.py sample --output my_components.csv
   ```

2. Edit the CSV file to match your aircraft components

3. Create a CG model with your components:
   ```bash
   python src/cg_calculator/main.py create --name "My Aircraft" --components my_components.csv
   ```

4. Add a 3D model (optional):
   ```bash
   python src/cg_calculator/main.py load --model outputs/cg_calculator/model.json --3d-model my_aircraft.stl
   ```

5. Visualize the CG:
   ```bash
   python src/cg_calculator/main.py visualize --model outputs/cg_calculator/model.json
   ```

6. Create an animation showing CG shift during consumption:
   ```bash
   python src/cg_calculator/main.py visualize --model outputs/cg_calculator/model.json --animate
   ```

## Tips for Accurate CG Calculation

1. Use consistent units throughout (either metric or imperial)
2. Define the coordinate system clearly (typically, X-axis is along the fuselage, Y-axis is along the wingspan, Z-axis is vertical)
3. Choose a sensible reference point (often the nose of the aircraft or a datum defined in the aircraft manual)
4. Include all significant components, especially heavy items
5. For consumable items like fuel, set the `is_consumable` flag to "True" and specify the `consumption_rate`

## Troubleshooting

- If you encounter issues with 3D model import, try converting your model to STL format
- Ensure your component coordinates use the same reference system as your 3D model
- For large models, you may need to adjust the visualization settings in the `visualization.py` file
