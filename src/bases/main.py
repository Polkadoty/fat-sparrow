import numpy as np
from grid_system import GridSystem
from optimization import OptimizationSystem
from visualization import Visualizer

def main():
    grid = GridSystem()
    optimizer = OptimizationSystem(grid)
    visualizer = Visualizer(grid)
    
    print("Starting optimization process...")
    
    # Find minimum number of bases needed
    best_solution = optimizer.find_minimum_bases(max_bases=18)
    
    if not best_solution:
        print("No perfect solution found, using best attempt...")
        best_solution = {
            'sites': optimizer.best_sites,
            'num_sites': len(optimizer.best_sites),
            'coverage': optimizer.best_coverage
        }
    
    print(f"\nBest Solution Found:")
    print(f"Number of Sites: {best_solution['num_sites']}")
    print(f"Coverage Score: {best_solution['coverage']:.2f}")
    
    # Save optimization animation as gif
    visualizer.save_optimization_animation(optimizer, 'optimization.gif')
    
    # Save final coverage heatmap as svg
    visualizer.plot_and_save_coverage_heatmap(best_solution['sites'], 'coverage.svg')

if __name__ == "__main__":
    main()  