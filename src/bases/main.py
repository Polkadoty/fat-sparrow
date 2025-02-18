import numpy as np
from grid_system import GridSystem
from optimization import OptimizationSystem
from visualization import Visualizer
import os

def main():
    # Create output directories
    os.makedirs('outputs/base_optimization', exist_ok=True)
    os.makedirs('outputs/base_coverage', exist_ok=True)
    
    grid = GridSystem()
    optimizer = OptimizationSystem(grid)
    visualizer = Visualizer(grid)
    
    print("Starting optimization process...")
    
    # Find minimum number of bases needed
    best_solution = optimizer.find_minimum_bases(max_bases=16)
    
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
    
    # Save outputs to appropriate subdirectories
    visualizer.save_coverage_metrics_animation(
        best_solution['metrics_history'],
        'outputs/base_optimization/coverage_metrics.gif'
    )
    
    visualizer.save_optimization_animation(
        optimizer, 
        'outputs/base_optimization/optimization.gif'
    )
    
    visualizer.plot_and_save_coverage_heatmap(
        best_solution['sites'], 
        'outputs/base_coverage/coverage.svg'
    )

if __name__ == "__main__":
    main()  