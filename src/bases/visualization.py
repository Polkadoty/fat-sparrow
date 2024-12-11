import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
import matplotlib.colors as colors
from typing import List, Tuple, Dict
from grid_system import GridSystem
import os

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
        
        # Combine histories from all base numbers, taking only 5 samples per base number
        current_base_count = None
        current_base_frames = []
        
        for sites_list in optimizer.base_history:
            num_bases = len(sites_list)
            if num_bases != current_base_count:
                if current_base_frames:
                    # Sample 5 frames from previous base count
                    indices = np.linspace(0, len(current_base_frames)-1, 5, dtype=int)
                    all_history.extend([current_base_frames[i] for i in indices])
                current_base_count = num_bases
                current_base_frames = [sites_list]
            else:
                current_base_frames.append(sites_list)
        
        # Add remaining frames
        if current_base_frames:
            indices = np.linspace(0, len(current_base_frames)-1, 5, dtype=int)
            all_history.extend([current_base_frames[i] for i in indices])
        
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
        """Plot coverage heatmap with wind-adjusted range circles"""
        plt.figure(figsize=(12, 10))
        
        # Set launch sites and get coverage
        self.grid.launch_sites = sites
        coverage_counts = self.grid.get_coverage_counts()
        
        # Plot heatmap
        extent = [0, self.grid.AREA_SIZE_NM, 0, self.grid.AREA_SIZE_NM]
        im = plt.imshow(coverage_counts.T,
                       extent=extent,
                       origin='lower',
                       cmap='RdYlBu')
        
        # Plot base locations and wind-adjusted range ellipses
        for site in sites:
            x_nm = site[0] / self.grid.NM_TO_METERS
            y_nm = site[1] / self.grid.NM_TO_METERS
            
            # Create points for wind-adjusted range
            angles = np.linspace(0, 2*np.pi, 100)
            range_points_x = []
            range_points_y = []
            
            for angle in angles:
                # Create point at max range
                dx = np.cos(angle) * self.grid.max_range
                dy = np.sin(angle) * self.grid.max_range
                point = (site[0] + dx, site[1] + dy)
                
                # Adjust for wind
                wind_adjusted_dist = self.grid.calculate_wind_adjusted_distance(site, point)
                scale_factor = self.grid.max_range / wind_adjusted_dist
                
                range_points_x.append((site[0] + dx * scale_factor) / self.grid.NM_TO_METERS)
                range_points_y.append((site[1] + dy * scale_factor) / self.grid.NM_TO_METERS)
            
            # Plot wind-adjusted range
            plt.plot(range_points_x, range_points_y, '--', color='black', alpha=0.5)
            
            # Plot base location
            plt.plot(x_nm, y_nm, 'k^', markersize=10)
        
        # Add wind vector arrow
        wind_speed_nm = self.grid.wind_speed_knots / 3600  # Convert to NM/s
        center_x = self.grid.AREA_SIZE_NM / 2
        center_y = self.grid.AREA_SIZE_NM / 2
        wind_dx = np.cos(self.grid.wind_direction) * wind_speed_nm * 3600  # Scale for visibility
        wind_dy = np.sin(self.grid.wind_direction) * wind_speed_nm * 3600
        
        plt.arrow(center_x, center_y, wind_dx, wind_dy, 
                 head_width=0.5, head_length=0.8, fc='red', ec='red', alpha=0.7)
        
        plt.colorbar(im, label='Number of Bases in Range')
        plt.title(f'Coverage Map - {len(sites)} Bases\n'
                 f'Wind: {self.grid.wind_speed_knots:.0f} kts @ {np.degrees(self.grid.wind_direction):.0f}°')
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

    def animate_coverage_metrics(self, metrics_history):
        """Create animated line plot of coverage metrics"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        def update(frame):
            ax.clear()
            # Use actual frame number for all frames except the last few
            if frame < len(metrics_history['num_bases']):
                end_idx = frame + 1
            else:
                # For extra frames, keep showing the final state
                end_idx = len(metrics_history['num_bases'])
            
            # Plot lines
            ax.plot(metrics_history['num_bases'][:end_idx], 
                    np.array(metrics_history['optimal_coverage'][:end_idx]) * 100,
                    'g-', label='Optimal Coverage (5)')
            ax.plot(metrics_history['num_bases'][:end_idx],
                    np.array(metrics_history['under_coverage'][:end_idx]) * 100,
                    'r-', label='Under Coverage (<5)')
            ax.plot(metrics_history['num_bases'][:end_idx],
                    np.array(metrics_history['over_coverage'][:end_idx]) * 100,
                    'b-', label='Over Coverage (>5)')
            
            ax.set_xlabel('Number of Bases')
            ax.set_ylabel('Coverage (%)')
            ax.set_title('Coverage Metrics vs Number of Bases')
            ax.grid(True)
            ax.legend()
            ax.set_ylim(0, 100)
            
            return []
        
        # Add 10 extra frames at the end
        total_frames = len(metrics_history['num_bases']) + 10
        anim = FuncAnimation(fig, update,
                            frames=total_frames,
                            interval=200,
                            repeat=False)
        
        return anim, fig

    def save_coverage_metrics_animation(self, metrics_history, filename='outputs/coverage_metrics.gif'):
        """Save coverage metrics animation as gif and final frame as png"""
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        anim, fig = self.animate_coverage_metrics(metrics_history)
        
        # Save the animation
        anim.save(filename, writer='pillow', fps=5)
        
        # Save the final frame as high-quality PNG
        png_filename = filename.replace('.gif', '_final.png')
        
        # Create the final frame
        update = anim._func  # Get the update function
        update(len(metrics_history['num_bases']))  # Update to final state
        
        # Save as high-quality PNG
        fig.savefig(png_filename, dpi=300, bbox_inches='tight')
        plt.close(fig)