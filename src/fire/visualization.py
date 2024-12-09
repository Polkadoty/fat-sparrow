import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import FancyArrowPatch
from fire_system import FireSystem, WindConditions

class FireVisualizer:
    def __init__(self, fire_system: FireSystem):
        self.fire_system = fire_system
        self.fig, self.ax = plt.subplots(figsize=(12, 12))
        self.im = None
        self.wind_arrow = None
        self.wind_text = None
        self.time_text = None
        self.wind_conditions = WindConditions.generate_initial()
        self.elapsed_time = 0
        self.suppressant_phase = False
        self.final_countdown = False
        
    def _create_visualization_matrix(self):
        """Create visualization matrix combining temperature and burning state"""
        vis_matrix = np.zeros((self.fire_system.grid_size, 
                             self.fire_system.grid_size, 4))
        
        for i in range(self.fire_system.grid_size):
            for j in range(self.fire_system.grid_size):
                temp = self.fire_system.temperature_grid[i, j]
                burning = self.fire_system.burning_grid[i, j]
                fuel = self.fire_system.fuel_grid[i, j]
                suppressant = self.fire_system.suppressant_grid[i, j]
                
                # Normalize temperature
                norm_temp = (temp - self.fire_system.AMBIENT_TEMP) / \
                          (self.fire_system.MAX_TEMP - self.fire_system.AMBIENT_TEMP)
                
                if suppressant > 0:
                    # White for suppressant
                    vis_matrix[i, j] = [1, 1, 1, 1]
                elif burning > 0:
                    # Red-yellow for active fire
                    vis_matrix[i, j] = [1, norm_temp * 0.8, 0, 1]
                else:
                    # Brown for fuel, darker when more fuel available
                    vis_matrix[i, j] = [0.5 * fuel, 0.3 * fuel, 0, 1]
        
        return vis_matrix

    def update_frame(self, frame):
        # Update elapsed time (10 seconds per frame)
        self.elapsed_time += 10
        
        # Start suppressant phase at 7 minutes
        if self.elapsed_time >= 420 and not self.suppressant_phase:
            self.suppressant_phase = True
            
        # Start final countdown at 7 minutes
        if self.elapsed_time >= 420 and not self.final_countdown:
            self.final_countdown = True
            
        # End simulation at 10 minutes
        if self.elapsed_time >= 600:
            plt.text(0.5, 0.5, f'Total Suppressants Used: {self.fire_system.suppressant_count}',
                    transform=self.ax.transAxes, ha='center', va='center',
                    bbox=dict(facecolor='white', alpha=0.9), fontsize=14)
            return [self.im]
            
        # Update wind conditions
        self.wind_conditions.update(dt=10.0)
        
        # Update fire state
        self.fire_system.update(self.wind_conditions, dt=10.0)
        
        if self.suppressant_phase:
            self.fire_system.deploy_suppressants(self.wind_conditions)
        
        # Clear previous arrow and text
        if self.wind_arrow:
            self.wind_arrow.remove()
        if self.wind_text:
            self.wind_text.remove()
        
        # Update visualization matrix
        vis_matrix = self._create_visualization_matrix()
        
        if self.im is None:
            self.im = self.ax.imshow(vis_matrix)
        else:
            self.im.set_array(vis_matrix)
            
        # Add larger wind direction arrow in center
        center = self.fire_system.grid_size // 2
        arrow_length = 12 * (self.wind_conditions.speed / (16 * 0.514))  # Increased base length
        dx = arrow_length * np.cos(self.wind_conditions.direction)
        dy = arrow_length * np.sin(self.wind_conditions.direction)
        
        # Create fancy red arrow
        self.wind_arrow = FancyArrowPatch(
            (center, center),
            (center + dx, center + dy),
            arrowstyle='fancy,head_length=0.8,head_width=0.6',
            color='red',
            linewidth=2,
            zorder=5
        )
        self.ax.add_patch(self.wind_arrow)
        
        # Add wind information text
        wind_speed_knots = self.wind_conditions.speed / 0.514  # Convert m/s to knots
        base_speed_knots = self.wind_conditions.base_speed / 0.514
        wind_deg = np.degrees(self.wind_conditions.direction)
        self.wind_text = self.ax.text(
            0.5, 1.05,
            f'Wind: {wind_speed_knots:.1f} kts (Base: {base_speed_knots:.1f} kts)  @ {wind_deg:.0f}°',
            transform=self.ax.transAxes,
            ha='center', va='bottom',
            bbox=dict(facecolor='white', alpha=0.7)
        )
        
        # Update title with wind information
        base_speed_kts = self.wind_conditions.base_speed / 0.514
        current_speed_kts = self.wind_conditions.speed / 0.514
        wind_deg = np.degrees(self.wind_conditions.direction)
        
        plt.title(f'Fire Spread Simulation\n'
                 f'Base Wind: {base_speed_kts:.1f}kts @ {wind_deg:.0f}°\n'
                 f'Current Wind: {current_speed_kts:.1f}kts\n'
                 f'Time: {self.elapsed_time//60:02d}:{self.elapsed_time%60:02d}')
        
        # Add or update time counter
        if self.time_text:
            self.time_text.remove()
        self.time_text = self.ax.text(
            0.02, 0.98, f'T+{self.elapsed_time//60:02d}:{self.elapsed_time%60:02d}',
            transform=self.ax.transAxes,
            color='white', fontsize=12,
            bbox=dict(facecolor='black', alpha=0.7)
        )
        
        return [self.im, self.wind_arrow, self.wind_text, self.time_text]
    
    def animate_fire(self, frames=60, interval=100):  # 60 frames * 10 seconds = 10 minutes
        """Animate fire spread for 10 minutes"""
        anim = FuncAnimation(self.fig, self.update_frame,
                           frames=frames, interval=interval,
                           blit=True)
        plt.colorbar(self.im)
        plt.title('Fire Spread Simulation')
        plt.show()
        return anim