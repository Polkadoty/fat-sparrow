import numpy as np
from perlin_noise import PerlinNoise
from dataclasses import dataclass
from typing import Tuple
import random

@dataclass
class WindConditions:
    speed: float      # m/s
    direction: float  # radians
    base_speed: float # base wind speed without gusts
    base_direction: float # base wind direction
    last_wobble: float = 0  # Time tracker for wind direction changes
    
    @classmethod
    def generate_initial(cls):
        """Generate initial wind conditions with speed 0-16 knots"""
        base_speed = random.uniform(0, 16) * 0.514  # Convert knots to m/s
        base_direction = random.uniform(0, 2 * np.pi)
        return cls(base_speed, base_direction, base_speed, base_direction, 0)
    
    def update(self, dt: float):
        """Update wind conditions with more realistic variations"""
        self.last_wobble += dt
        
        # Wobble direction every 20 seconds
        if self.last_wobble >= 20:
            self.last_wobble = 0
            # Reduced direction variation (±15 degrees)
            direction_change = random.uniform(-np.pi/12, np.pi/12)
            self.direction = self.base_direction + direction_change
            
            # Scale speed variations with base speed
            max_variation = self.base_speed * 0.2  # 20% of base speed
            speed_change = random.uniform(-max_variation, max_variation)
            self.speed = np.clip(self.base_speed + speed_change, 0, 16 * 0.514)

class FireSystem:
    def __init__(self, grid_size: int = 150):
        self.grid_size = grid_size
        self.cell_size = 1.0  # meters
        self.time_per_step = 10.0  # seconds per frame
        
        # Main grids
        self.temperature_grid = np.zeros((grid_size, grid_size))
        self.fuel_grid = np.zeros((grid_size, grid_size))
        self.humidity_grid = np.zeros((grid_size, grid_size))
        self.burning_grid = np.zeros((grid_size, grid_size))
        self.suppressant_grid = np.zeros((grid_size, grid_size))
        
        # Constants based on research (adjusted for 10-second timesteps)
        self.IGNITION_TEMP = 300
        self.MAX_TEMP = 800
        self.AMBIENT_TEMP = 25
        self.COOLING_RATE = 0.005 * self.time_per_step
        self.WIND_FACTOR = 0.6
        self.BASE_SPREAD_RATE = 2.0
        self.FUEL_CONSUMPTION_RATE = 0.025
        self.SUPPRESSANT_RADIUS = 1
        self.SUPPRESSANT_PER_FRAME = 8  # Increased from 5
        self.LOOK_AHEAD_DISTANCE = 12
        self.line_length = 5  # Initial line length (will grow)
        self.arc_radius = self.line_length  # Initial arc radius
        self.arc_angle = np.pi/3  # 60-degree arc
        
        self.suppressant_count = 0
        self.grid_center = (grid_size // 2, grid_size // 2)  # Store grid center
        self.initial_suppressant_point = None  # Track where we started dropping
        
        self._initialize_terrain()
    
    def _initialize_terrain(self):
        """Generate realistic terrain features using simplified noise patterns"""
        # Create two main noise layers
        terrain_noise = PerlinNoise(octaves=4, seed=1)
        moisture_noise = PerlinNoise(octaves=3, seed=2)
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Use larger scale for more distinct patterns
                nx = i / 50  # Increased scale for more visible patterns
                ny = j / 50
                
                # Generate base terrain with more contrast
                terrain = terrain_noise([nx, ny])
                moisture = moisture_noise([nx * 1.5, ny * 1.5])  # Slightly different scale
                
                # Normalize and enhance contrast
                terrain = self._normalize_noise(terrain, 0.3, 1.0)
                moisture = self._normalize_noise(moisture, 0.2, 0.9)
                
                # Create more distinct patterns
                self.humidity_grid[i, j] = moisture
                self.fuel_grid[i, j] = terrain * (1 - moisture * 0.6)  # Less moisture impact
    
    def _normalize_noise(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize noise value to desired range"""
        return min_val + (max_val - min_val) * (value + 1) / 2
    
    def start_fire(self, position: Tuple[int, int], radius: int = 10):
        """Start a fire at given position with specified radius (default 10m for 20x20m square)"""
        x, y = position
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                if i*i + j*j <= radius*radius:  # Circular fire
                    xi, yj = x + i, y + j
                    if 0 <= xi < self.grid_size and 0 <= yj < self.grid_size:
                        self.temperature_grid[xi, yj] = self.MAX_TEMP
                        self.burning_grid[xi, yj] = 1.0

    def update(self, wind: WindConditions, dt: float = 10.0):
        """Update fire state including suppressant effects"""
        new_temp = np.copy(self.temperature_grid)
        new_burning = np.copy(self.burning_grid)
        
        # Check suppressant effects first
        burning_locations = np.where(self.burning_grid > 0)
        for i, j in zip(*burning_locations):
            # Check non-diagonal neighbors for suppressant
            neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            for di, dj in neighbors:
                ni, nj = i + di, j + dj
                if (0 <= ni < self.grid_size and 0 <= nj < self.grid_size and 
                    self.suppressant_grid[ni, nj] > 0):
                    new_burning[i, j] = 0
                    new_temp[i, j] = self.AMBIENT_TEMP
                    break
        
        # Update burning state and spread fire
        burning_locations = np.where(self.burning_grid > 0)
        for i, j in zip(*burning_locations):
            # Consume fuel
            self.fuel_grid[i, j] = max(0, self.fuel_grid[i, j] - self.FUEL_CONSUMPTION_RATE)
            
            # Stop burning if no fuel
            if self.fuel_grid[i, j] <= 0:
                new_burning[i, j] = 0
                new_temp[i, j] = self.AMBIENT_TEMP
            else:
                # Spread fire to neighbors
                self._spread_fire(i, j, wind, new_temp, new_burning)
                
            # Cooling
            if new_burning[i, j] == 0:
                new_temp[i, j] = max(self.AMBIENT_TEMP,
                                   new_temp[i, j] - self.COOLING_RATE)
        
        self.temperature_grid = new_temp
        self.burning_grid = new_burning
    
    def _spread_fire(self, i: int, j: int, wind: WindConditions, 
                    new_temp: np.ndarray, new_burning: np.ndarray):
        """Calculate fire spread with realistic rates based on research"""
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                    
                ni, nj = i + di, j + dj
                if not (0 <= ni < self.grid_size and 0 <= nj < self.grid_size):
                    continue
                
                # Check if there's a suppressant in the path
                if self._check_suppressant_line(i, j, ni, nj):
                    continue
                
                base_prob = (self.BASE_SPREAD_RATE * self.time_per_step) / 60.0
                
                # Wind speed categories and multipliers (based on research)
                wind_speed_knots = wind.speed / 0.514
                if wind_speed_knots < 5:
                    speed_mult = 1.0
                elif wind_speed_knots < 10:
                    speed_mult = 3.0
                else:
                    speed_mult = 8.0
                
                # Wind alignment effect
                wind_alignment = self._calculate_wind_alignment(di, dj, wind.direction)
                if wind_alignment > 0.7:  # Downwind
                    wind_mult = speed_mult
                elif wind_alignment < -0.7:  # Upwind
                    wind_mult = 0.01 / (1 + wind_speed_knots/5)  # Very unlikely against wind
                else:  # Crosswind
                    wind_mult = 0.1 * speed_mult  # Reduced from 0.4 to 0.1
                
                # Environmental factors
                humidity_factor = 1 - self.humidity_grid[ni, nj]
                fuel_factor = self.fuel_grid[ni, nj]
                
                spread_prob = base_prob * wind_mult * humidity_factor * fuel_factor
                
                if np.random.random() < spread_prob and self.burning_grid[ni, nj] == 0:
                    new_temp[ni, nj] = min(self.MAX_TEMP, 
                                         new_temp[ni, nj] + 300)
                    if new_temp[ni, nj] >= self.IGNITION_TEMP:
                        new_burning[ni, nj] = 1.0

    def _check_suppressant_line(self, i1: int, j1: int, i2: int, j2: int) -> bool:
        """Check if there's a suppressant between two points"""
        # Check points along the line between the two cells
        points = np.linspace((i1, j1), (i2, j2), 5)
        for i, j in points:
            ii, jj = int(round(i)), int(round(j))
            if self.suppressant_grid[ii, jj]:
                return True
        return False
    
    def _calculate_wind_alignment(self, di: int, dj: int, wind_direction: float) -> float:
        """Calculate alignment between spread direction and wind direction"""
        if di == 0 and dj == 0:
            return 0
        
        # Convert to meteorological convention (0° = North, clockwise positive)
        # Note: Grid uses -j as North direction
        spread_direction = np.arctan2(-di, -dj)  # Convert to meteorological convention
        if spread_direction < 0:
            spread_direction += 2 * np.pi
        
        # Normalize wind direction to [0, 2π]
        wind_direction = wind_direction % (2 * np.pi)
        
        # Calculate smallest angle between directions
        angle_diff = abs(spread_direction - wind_direction)
        if angle_diff > np.pi:
            angle_diff = 2 * np.pi - angle_diff
        
        # Return cosine of angle difference
        return np.cos(angle_diff)
    
    def deploy_suppressants(self, wind: WindConditions):
        """Deploy suppressants focusing on fire expansion direction"""
        if self.suppressant_count >= 50:
            return
        
        burning_locations = np.where(self.burning_grid > 0)
        if len(burning_locations[0]) == 0:
            return
        
        # Calculate center of fire mass
        center_i = np.mean(burning_locations[0])
        center_j = np.mean(burning_locations[1])
        
        # Calculate point furthest in wind direction
        max_projection = float('-inf')
        furthest_point = None
        
        # Wind direction vector (meteorological convention)
        wind_i = -np.sin(wind.direction)
        wind_j = -np.cos(wind.direction)
        
        # Find furthest burning point in wind direction
        for i, j in zip(*burning_locations):
            projection = (i - center_i) * wind_i + (j - center_j) * wind_j
            if projection > max_projection:
                max_projection = projection
                furthest_point = (i, j)
        
        if furthest_point is None:
            return
        
        # Place line 12 meters ahead in wind direction
        fi, fj = furthest_point
        start_i = int(fi + wind_i * 12)
        start_j = int(fj + wind_j * 12)
        
        # Create perpendicular vector for the line
        perp_i = -wind_j
        perp_j = wind_i
        
        # Deploy suppressants with focus on wind direction
        line_length = 25
        for t in range(-line_length, line_length + 1, 3):
            # Adjust curve to focus more on the wind direction side
            if t > 0:  # Downwind side
                curve_factor = -(t ** 2) / (3 * line_length)  # Stronger curve downwind
                spacing = 2  # Closer spacing
            else:  # Upwind side
                curve_factor = -(t ** 2) / (6 * line_length)  # Weaker curve upwind
                spacing = 4  # Wider spacing
            
            point_i = int(start_i + perp_i * t + wind_i * curve_factor)
            point_j = int(start_j + perp_j * t + wind_j * curve_factor)
            
            if (0 <= point_i < self.grid_size and 
                0 <= point_j < self.grid_size and
                self.suppressant_count < 50):
                # Create plus pattern
                for di, dj in [(0,0), (1,0), (-1,0), (0,1), (0,-1)]:
                    ni, nj = point_i + di, point_j + dj
                    if (0 <= ni < self.grid_size and 
                        0 <= nj < self.grid_size):
                        self.suppressant_grid[ni, nj] = 1
                self.suppressant_count += 1