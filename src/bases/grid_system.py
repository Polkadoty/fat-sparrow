import numpy as np
from typing import Tuple, List

class GridSystem:
    # Constants
    NM_TO_METERS = 1852  # 1 nautical mile = 1852 meters
    AREA_SIZE_NM = 17.06  # Size of area in nautical miles
    GRID_RESOLUTION = 473  # Changed to 0.5 NM resolution (1852 / 2)
    AIRCRAFT_SPEED = 60  # Speed in knots
    def __init__(self):
        self.area_size_meters = self.AREA_SIZE_NM * self.NM_TO_METERS
        self.grid_points = int(self.area_size_meters / self.GRID_RESOLUTION)
        self.grid = np.zeros((self.grid_points, self.grid_points))
        self.launch_sites: List[Tuple[float, float]] = []
        
        # Calculate fixed range circle
        speed_mps = self.AIRCRAFT_SPEED * self.NM_TO_METERS / 3600
        remaining_time = 420  # 7 minutes after launch
        self.max_range = speed_mps * remaining_time

    def get_coverage_counts(self) -> np.ndarray:
        """Return matrix showing how many bases can reach each point"""
        coverage_counts = np.zeros((self.grid_points, self.grid_points))
        
        for i in range(self.grid_points):
            for j in range(self.grid_points):
                point = (i * self.GRID_RESOLUTION, j * self.GRID_RESOLUTION)
                for site in self.launch_sites:
                    if self.calculate_distance(point, site) <= self.max_range:
                        coverage_counts[i, j] += 1
        
        return coverage_counts

    def check_coverage_requirement(self, min_bases_required: int) -> bool:
        """Check if each point is covered by at least min_bases_required bases"""
        coverage_counts = self.get_coverage_counts()
        return np.all(coverage_counts >= min_bases_required)
    
    def get_random_fire_location(self) -> Tuple[float, float]:
        """Generate a random fire location within the grid"""
        x = np.random.uniform(0, self.area_size_meters)
        y = np.random.uniform(0, self.area_size_meters)
        return (x, y)
    
    def add_launch_site(self, x: float, y: float) -> bool:
        """Add a launch site to the grid if it's within bounds"""
        if 0 <= x <= self.area_size_meters and 0 <= y <= self.area_size_meters:
            self.launch_sites.append((x, y))
            return True
        return False
    
    def calculate_distance(self, point1: Tuple[float, float], 
                         point2: Tuple[float, float]) -> float:
        """Calculate straight-line distance between two points in meters"""
        return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
    
    def get_coverage_matrix(self, speed_knots: float, 
                          launch_time: float = 30) -> np.ndarray:
        """
        Calculate coverage matrix showing areas reachable within time limit
        
        Args:
            speed_knots: Aircraft speed in knots
            launch_time: Launch time in seconds
        
        Returns:
            Binary matrix where 1 indicates covered areas
        """
        speed_mps = speed_knots * self.NM_TO_METERS / 3600  # Convert knots to m/s
        remaining_time = 600 - launch_time  # 10 minutes - launch time in seconds
        max_distance = speed_mps * remaining_time
        
        coverage = np.zeros((self.grid_points, self.grid_points))
        
        for i in range(self.grid_points):
            for j in range(self.grid_points):
                point = (i * self.GRID_RESOLUTION, j * self.GRID_RESOLUTION)
                for site in self.launch_sites:
                    if self.calculate_distance(point, site) <= max_distance:
                        coverage[i, j] = 1
                        break
                        
        return coverage 