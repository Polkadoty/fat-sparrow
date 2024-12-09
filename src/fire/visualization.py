import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import FancyArrowPatch
from fire_system import FireSystem, WindConditions
from matplotlib import animation

class FireVisualizer:
    def __init__(self, fire_system: FireSystem):
        self.fire_system = fire_system
        # Create figure with extra space on right for legend
        self.fig, self.ax = plt.subplots(figsize=(14, 12))
        self.im = None
        self.wind_arrow = None
        self.wind_text = None
        self.time_text = None
        self.wind_conditions = WindConditions.generate_initial()
        self.elapsed_time = 0
        self.suppressant_phase = False
        self.final_countdown = False
        # Adjust subplot parameters to make room for legend
        plt.subplots_adjust(right=0.85)
        
    def _create_visualization_matrix(self):
        """Create visualization matrix with distinct terrain patterns and burnt areas"""
        vis_matrix = np.zeros((self.fire_system.grid_size, 
                             self.fire_system.grid_size, 4))
        
        # First pass: Create base terrain
        for i in range(self.fire_system.grid_size):
            for j in range(self.fire_system.grid_size):
                humidity = self.fire_system.humidity_grid[i, j]
                fuel = self.fire_system.fuel_grid[i, j]
                
                # Darker terrain coloring
                if humidity > 0.6:  # High humidity areas
                    green = 0.25 + (humidity * 0.3)  # Darker green
                    brown = 0.2 + (0.1 * fuel)
                else:  # Drier areas
                    green = 0.15 + (humidity * 0.2)
                    brown = 0.3 + (fuel * 0.3)
                
                vis_matrix[i, j] = [
                    brown,  # Red (brown)
                    green,  # Green (reduced)
                    0.05,   # Blue (minimal tint)
                    1.0     # Alpha
                ]
        
        # Second pass: Overlay fire effects
        for i in range(self.fire_system.grid_size):
            for j in range(self.fire_system.grid_size):
                temp = self.fire_system.temperature_grid[i, j]
                burning = self.fire_system.burning_grid[i, j]
                suppressant = self.fire_system.suppressant_grid[i, j]
                
                norm_temp = (temp - self.fire_system.AMBIENT_TEMP) / \
                          (self.fire_system.MAX_TEMP - self.fire_system.AMBIENT_TEMP)
                
                if suppressant > 0:
                    # White for suppressant
                    vis_matrix[i, j] = [1, 1, 1, 1]
                elif burning > 0:
                    # Red-yellow for active fire
                    vis_matrix[i, j] = [1, norm_temp * 0.8, 0, 1]
                elif self.fire_system.fuel_grid[i, j] < 0.1:  # Burnt area (low fuel)
                    # Black for burnt areas
                    vis_matrix[i, j] = [0, 0, 0, 1]
        
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
        
        plt.title(f'Base Wind: {base_speed_kts:.1f}kts @ {wind_deg:.0f}°\n'
                 f'Current Wind: {current_speed_kts:.1f}kts')
        
        # Update legend with clear positioning
        legend = self.ax.legend(
            handles=[
                plt.Rectangle((0,0),1,1, fc='white', label='Suppressant'),
                plt.Rectangle((0,0),1,1, fc='red', label='Active Fire'),
                plt.Rectangle((0,0),1,1, fc='black', label='Burnt Area'),
                plt.Rectangle((0,0),1,1, fc='darkgreen', label='High Humidity'),
                plt.Rectangle((0,0),1,1, fc='saddlebrown', label='Low Humidity')
            ],
            loc='center left',
            bbox_to_anchor=(1.05, 0.5),
            frameon=True,
            title='Legend'
        )
        
        # Add or update time counter
        if self.time_text:
            self.time_text.remove()
        self.time_text = self.ax.text(
            0.02, 0.98, f'T+{self.elapsed_time//60:02d}:{self.elapsed_time%60:02d}',
            transform=self.ax.transAxes,
            color='white', fontsize=12,
            bbox=dict(facecolor='black', alpha=0.7)
        )
        
        return [self.im, self.wind_arrow, self.wind_text, self.time_text, legend]
    
    def animate_fire(self, frames=60, interval=100):
        """Animate fire spread for 10 minutes"""
        # Create outputs directory if it doesn't exist
        import os
        os.makedirs('outputs', exist_ok=True)
        
        # Set a fixed DPI and figure size to ensure consistent dimensions
        self.fig.set_dpi(100)
        self.fig.set_size_inches(14, 12)
        
        # Create animation
        anim = FuncAnimation(self.fig, self.update_frame,
                           frames=frames, interval=interval,
                           blit=True)
        
        # Use PillowWriter for GIF creation
        writer = animation.PillowWriter(fps=30)
        anim.save('outputs/fire_spread.gif', writer=writer)
        
        plt.title('Fire Spread Simulation')
        plt.show()
        return anim

    def save_outputs(self):
        """Save final state and animation"""
        import os
        import imageio
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Save final state
        plt.savefig('outputs/final_state.png', bbox_inches='tight', dpi=300)
        
        # Save animation if frames were collected
        if hasattr(self, 'frames') and self.frames:
            imageio.mimsave('outputs/fire_spread.gif', self.frames, fps=10)