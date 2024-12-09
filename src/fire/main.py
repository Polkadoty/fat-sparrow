from fire_system import FireSystem, WindConditions
from visualization import FireVisualizer

def main():
    # Initialize fire system with 100x100m grid
    fire_system = FireSystem(grid_size=150)
    
    # Start a fire in the center with 10m radius (20x20m square)
    fire_system.start_fire((75, 75), radius=10)  # Adjusted center position for 150x150 grid
    
    # Create visualizer and run animation
    visualizer = FireVisualizer(fire_system)
    visualizer.animate_fire()

if __name__ == "__main__":
    main()
