import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
import matplotlib.colors as colors
from typing import List, Tuple, Dict
from grid_system import GridSystem

class Visualizer:
    def __init__(self, grid: GridSystem):
        self.grid = grid
        self.fig = None
        self.ax = None
    
    def animate_optimization_heatmap(self, optimizer):
        """Animate the base placement optimization process"""
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        
        # Initialize heatmap matrix
        density_matrix = np.zeros((self.grid.grid_points, self.grid.grid_points))
        all_history = []
        
        # Combine histories from all base numbers
        for sites_list in optimizer.base_history:
            all_history.append(sites_list)
        
        def update(frame):
            if frame < len(all_history):
                sites = all_history[frame]
                self.ax.clear()
                
                # Calculate coverage counts for current configuration
                self.grid.launch_sites = sites
                coverage_counts = self.grid.get_coverage_counts()
                
                # Plot coverage heatmap
                im = self.ax.imshow(coverage_counts.T, 
                             extent=[0, self.grid.AREA_SIZE_NM, 0, self.grid.AREA_SIZE_NM],
                             origin='lower',
                             cmap='RdYlBu_r',  # Changed colormap
                             vmin=0,
                             vmax=len(sites))
                
                # Plot current base locations
                for site in sites:
                    x_nm = site[0] / self.grid.NM_TO_METERS
                    y_nm = site[1] / self.grid.NM_TO_METERS
                    self.ax.plot(x_nm, y_nm, 'k^', markersize=10)
                
                self.ax.set_title(f'Optimization Progress - Frame {frame + 1}\n{len(sites)} Bases')
                self.ax.set_xlabel('Distance (NM)')
                self.ax.set_ylabel('Distance (NM)')
                self.ax.grid(True)
            
            return []
        
        anim = FuncAnimation(self.fig, update, 
                             frames=len(all_history),
                             interval=50,  # Faster animation (50ms between frames)
                             blit=True)
        plt.show()
        return anim

    def plot_coverage_heatmap(self, sites: List[Tuple[float, float]]):
        """Plot heatmap showing number of bases that can reach each point"""
        plt.figure(figsize=(12, 10))
        
        # Calculate coverage counts
        self.grid.launch_sites = sites
        coverage_counts = self.grid.get_coverage_counts()
        
        # Plot heatmap
        extent = [0, self.grid.AREA_SIZE_NM, 0, self.grid.AREA_SIZE_NM]
        im = plt.imshow(coverage_counts.T,
                       extent=extent,
                       origin='lower',
                       cmap='RdYlBu')
        
        # Plot base locations and range circles
        for site in sites:
            x_nm = site[0] / self.grid.NM_TO_METERS
            y_nm = site[1] / self.grid.NM_TO_METERS
            
            # Add range circle
            circle = Circle((x_nm, y_nm), 
                          self.grid.max_range / self.grid.NM_TO_METERS,
                          fill=False, color='black', alpha=0.5)
            plt.gca().add_patch(circle)
            
            # Plot base location
            plt.plot(x_nm, y_nm, 'k^', markersize=10)
        
        plt.colorbar(im, label='Number of Bases in Range')
        plt.title(f'Coverage Map - {len(sites)} Bases\n'
                 f'Aircraft Speed: {self.grid.AIRCRAFT_SPEED} knots')
        plt.xlabel('Distance (NM)')
        plt.ylabel('Distance (NM)')
        plt.grid(True)
        plt.show()

    def save_optimization_animation(self, optimizer, filename='optimization.gif'):
        """Save the optimization animation as a gif"""
        anim = self.animate_optimization_heatmap(optimizer)
        anim.save(filename, writer='pillow')

    def plot_and_save_coverage_heatmap(self, sites: List[Tuple[float, float]], filename='coverage.svg'):
        """Plot and save coverage heatmap as SVG"""
        self.plot_coverage_heatmap(sites)
        plt.savefig(filename, format='svg', bbox_inches='tight')
        plt.close()