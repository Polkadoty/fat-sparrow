import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
from typing import List, Tuple, Dict, Optional
import os
from cg_model import CGModel, Component

class CGVisualizer:
    """Visualize aircraft CG and components"""
    
    def __init__(self, model: CGModel):
        self.model = model
        self.fig = None
        self.ax = None
        self.mesh = None
        self.cg_marker = None
        self.component_markers = []
        self.category_colors = {
            "structure": "#1f77b4",  # blue
            "payload": "#ff7f0e",    # orange
            "fuel": "#2ca02c",       # green
            "equipment": "#d62728",  # red
            "crew": "#9467bd",       # purple
            "passenger": "#8c564b",  # brown
            "other": "#e377c2"       # pink
        }
    
    def set_mesh(self, mesh: trimesh.Trimesh) -> None:
        """Set the 3D model mesh for visualization"""
        self.mesh = mesh
    
    def _plot_mesh(self) -> None:
        """Plot the 3D model mesh"""
        if self.mesh is None:
            return
            
        # Convert trimesh to faces for matplotlib
        vertices = self.mesh.vertices
        faces = self.mesh.faces
        
        # Create a Poly3DCollection
        mesh_collection = Poly3DCollection(
            [vertices[face] for face in faces],
            alpha=0.3,
            edgecolor='k',
            linewidth=0.1,
            facecolor='gray'
        )
        self.ax.add_collection3d(mesh_collection)
    
    def _plot_components(self) -> None:
        """Plot the aircraft components"""
        self.component_markers = []
        
        for comp in self.model.components:
            # Get color from category or use component's color
            color = self.category_colors.get(comp.category, comp.color)
            
            # Plot component as a cube
            x, y, z = comp.location
            dx, dy, dz = comp.size
            
            # Create cube vertices
            vertices = [
                [x - dx/2, y - dy/2, z - dz/2],
                [x + dx/2, y - dy/2, z - dz/2],
                [x + dx/2, y + dy/2, z - dz/2],
                [x - dx/2, y + dy/2, z - dz/2],
                [x - dx/2, y - dy/2, z + dz/2],
                [x + dx/2, y - dy/2, z + dz/2],
                [x + dx/2, y + dy/2, z + dz/2],
                [x - dx/2, y + dy/2, z + dz/2]
            ]
            
            # Define the faces using vertices
            faces = [
                [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
                [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
                [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
                [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
                [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
                [vertices[1], vertices[2], vertices[6], vertices[5]]   # right
            ]
            
            # Create a Poly3DCollection for the component
            component_collection = Poly3DCollection(
                faces,
                alpha=0.7,
                edgecolor='k',
                linewidth=0.5,
                facecolor=color
            )
            self.ax.add_collection3d(component_collection)
            self.component_markers.append(component_collection)
            
            # Add text label for component
            self.ax.text(
                x, y, z + dz/2,
                comp.name,
                fontsize=8,
                ha='center',
                va='bottom'
            )
    
    def _plot_cg(self) -> None:
        """Plot the center of gravity"""
        cg = self.model.calculate_cg()
        
        # Plot CG as a red sphere
        self.cg_marker = self.ax.scatter(
            cg[0], cg[1], cg[2],
            color='red',
            s=100,
            marker='o',
            label='Center of Gravity'
        )
        
        # Add text label for CG
        self.ax.text(
            cg[0], cg[1], cg[2] + 0.1,
            f"CG: ({cg[0]:.2f}, {cg[1]:.2f}, {cg[2]:.2f})",
            fontsize=10,
            ha='center',
            va='bottom',
            color='red'
        )
    
    def _plot_category_cg(self) -> None:
        """Plot the center of gravity for each category"""
        category_cg = self.model.calculate_category_cg()
        
        for category, cg in category_cg.items():
            color = self.category_colors.get(category, "#e377c2")  # Default to pink
            
            # Plot category CG as a smaller sphere
            self.ax.scatter(
                cg[0], cg[1], cg[2],
                color=color,
                s=50,
                marker='o',
                label=f"{category.capitalize()} CG"
            )
    
    def _plot_reference_axes(self) -> None:
        """Plot reference axes"""
        # Get model bounds or use component bounds if no model
        if self.mesh is not None:
            bounds = self.mesh.bounds
            min_bound = bounds[0]
            max_bound = bounds[1]
        else:
            # Calculate bounds from components
            if not self.model.components:
                min_bound = np.array([-1, -1, -1])
                max_bound = np.array([1, 1, 1])
            else:
                locations = np.array([comp.location for comp in self.model.components])
                sizes = np.array([comp.size for comp in self.model.components])
                
                # Calculate min and max bounds
                min_locations = locations - sizes/2
                max_locations = locations + sizes/2
                
                min_bound = np.min(min_locations, axis=0)
                max_bound = np.max(max_locations, axis=0)
        
        # Add some margin
        margin = np.max(max_bound - min_bound) * 0.1
        min_bound -= margin
        max_bound += margin
        
        # Set axis limits
        self.ax.set_xlim(min_bound[0], max_bound[0])
        self.ax.set_ylim(min_bound[1], max_bound[1])
        self.ax.set_zlim(min_bound[2], max_bound[2])
        
        # Set labels
        self.ax.set_xlabel('X (Longitudinal)')
        self.ax.set_ylabel('Y (Lateral)')
        self.ax.set_zlabel('Z (Vertical)')
        
        # Add a grid
        self.ax.grid(True)
    
    def visualize_static(self) -> plt.Figure:
        """Create a static visualization of the aircraft and CG"""
        self.fig = plt.figure(figsize=(12, 10))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Plot the mesh if available
        self._plot_mesh()
        
        # Plot components
        self._plot_components()
        
        # Plot CG
        self._plot_cg()
        
        # Plot category CGs
        self._plot_category_cg()
        
        # Plot reference axes
        self._plot_reference_axes()
        
        # Add title
        self.ax.set_title(f"{self.model.aircraft_name} - Center of Gravity Analysis")
        
        # Add legend
        self.ax.legend()
        
        return self.fig
    
    def visualize_consumption(self, max_time: float = 5.0, steps: int = 50) -> FuncAnimation:
        """Create an animation showing CG shift during consumption"""
        self.fig = plt.figure(figsize=(12, 10))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Plot the mesh if available
        self._plot_mesh()
        
        # Plot components (initial state)
        self._plot_components()
        
        # Plot reference axes
        self._plot_reference_axes()
        
        # Initialize CG marker
        initial_cg = self.model.calculate_cg()
        self.cg_marker = self.ax.scatter(
            initial_cg[0], initial_cg[1], initial_cg[2],
            color='red',
            s=100,
            marker='o',
            label='Center of Gravity'
        )
        
        # Initialize CG path
        cg_path_x, cg_path_y, cg_path_z = [], [], []
        cg_path_line, = self.ax.plot([], [], [], 'r--', linewidth=1, alpha=0.5)
        
        # Initialize time text
        time_text = self.ax.text2D(0.05, 0.95, '', transform=self.ax.transAxes)
        
        # Add title
        self.ax.set_title(f"{self.model.aircraft_name} - CG Shift During Consumption")
        
        # Add legend
        self.ax.legend()
        
        def update(frame):
            # Calculate time
            time = frame * max_time / steps
            
            # Calculate CG at this time
            cg = self.model.simulate_consumption(time)
            
            # Update CG marker
            self.cg_marker._offsets3d = ([cg[0]], [cg[1]], [cg[2]])
            
            # Update CG path
            cg_path_x.append(cg[0])
            cg_path_y.append(cg[1])
            cg_path_z.append(cg[2])
            cg_path_line.set_data_3d(cg_path_x, cg_path_y, cg_path_z)
            
            # Update time text
            time_text.set_text(f'Time: {time:.1f} hours')
            
            return self.cg_marker, cg_path_line, time_text
        
        # Create animation
        anim = FuncAnimation(
            self.fig, update, frames=steps+1,
            interval=100, blit=True
        )
        
        return anim
    
    def save_static_visualization(self, filename: str) -> None:
        """Save the static visualization to a file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Create visualization if not already created
        if self.fig is None:
            self.visualize_static()
        
        # Save figure
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved visualization to {filename}")
    
    def save_consumption_animation(self, filename: str, max_time: float = 5.0, steps: int = 50) -> None:
        """Save the consumption animation to a file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Create animation
        anim = self.visualize_consumption(max_time, steps)
        
        # Save animation
        anim.save(filename, writer='pillow', fps=10)
        print(f"Saved animation to {filename}") 