import numpy as np
from typing import Tuple, List
from grid_system import GridSystem

class OptimizationSystem:
    def __init__(self, grid: GridSystem):
        self.grid = grid
        self.best_coverage = 0
        self.best_sites = []
        self.best_num_sites = 0
        self.optimal_solutions = []
        self.base_history = []
        
    def calculate_radial_probability(self, r: float, max_radius: float) -> float:
        """Calculate probability of placing base at given radius"""
        # Normalize radius to [0,1]
        r_norm = r / max_radius
        
        # Parameters for ring-shaped distribution
        peak_radius = 0.67  # Peak probability at 2/3 of max radius
        spread = 0.45      # Wider spread for more natural distribution
        
        # Calculate gaussian probability centered at peak_radius
        prob = np.exp(-((r_norm - peak_radius)**2) / (2 * spread**2))
        
        # Gentle reduction at edges
        edge_penalty = np.exp(-((1-r_norm)**2) / 0.1)  # Softer edge penalty
        return prob - edge_penalty * 0.15

    def generate_initial_sites(self, num_sites: int = 4) -> List[Tuple[float, float]]:
        """Generate initial launch sites using radial distribution"""
        sites = []
        max_radius = min(self.grid.area_size_meters / 2.2,
                        self.grid.max_range * 1.1)
        center = (self.grid.area_size_meters / 2, self.grid.area_size_meters / 2)
        
        # Generate sites using radial distribution
        angles = np.linspace(0, 2 * np.pi, num_sites, endpoint=False)
        np.random.shuffle(angles)
        
        for angle in angles:
            while True:
                # Increased minimum radius to avoid center clustering
                radius = np.random.uniform(0.4 * max_radius, max_radius)
                prob = self.calculate_radial_probability(radius, max_radius)
                if np.random.random() < prob:
                    break
            
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            
            # Ensure within bounds with larger margin
            margin = self.grid.max_range * 0.2  # Increased margin
            x = np.clip(x, margin, self.grid.area_size_meters - margin)
            y = np.clip(y, margin, self.grid.area_size_meters - margin)
            
            sites.append((x, y))
        
        return sites

    def optimize_sites(self, num_sites: int, iterations: int = 100) -> Tuple[List[Tuple[float, float]], float]:
        """Optimize launch site locations"""
        valid_iterations = 0
        total_attempts = 0
        max_attempts = iterations * 4  # Limit total attempts to prevent infinite loops
        
        current_sites = self.generate_initial_sites(num_sites)
        self.grid.launch_sites = current_sites.copy()  # Make sure to copy the list
        
        temperature = 3.0
        cooling_rate = 0.99
        
        best_coverage = float('-inf')
        best_sites = None
        
        while valid_iterations < iterations and total_attempts < max_attempts:
            total_attempts += 1
            
            coverage_counts = self.grid.get_coverage_counts()
            if np.sum(coverage_counts == 0) > 0:
                # Try new configuration if there's zero coverage
                current_sites = self.generate_initial_sites(num_sites)
                self.grid.launch_sites = current_sites.copy()
                continue
            
            valid_iterations += 1
            if valid_iterations % 10 == 0:
                print(f"Valid iteration {valid_iterations}/{iterations}")
            
            current_score = self.calculate_score(coverage_counts, num_sites)
            
            if current_score > best_coverage:
                best_coverage = current_score
                best_sites = current_sites.copy()
                print(f"New best solution! Score: {current_score:.2f}")
            
            # Generate new configuration
            new_sites = self.generate_initial_sites(num_sites)
            self.grid.launch_sites = new_sites.copy()
            
            coverage_counts = self.grid.get_coverage_counts()
            if np.sum(coverage_counts == 0) > 0:
                continue
            
            new_score = self.calculate_score(coverage_counts, num_sites)
            
            delta = new_score - current_score
            if delta > 0 or np.random.random() < np.exp(delta / temperature):
                current_sites = new_sites.copy()
                if best_sites is not None:  # Only append to history if we have a valid solution
                    self.base_history.append(new_sites)
            
            temperature *= cooling_rate
        
        if best_sites is None:
            return current_sites, float('-inf')
        
        return best_sites, best_coverage / (self.grid.grid_points ** 2)

    def find_minimum_bases(self, max_bases: int = 16) -> dict:
        """Find optimal number of bases where over/under coverage lines intersect"""
        print("\nSearching for optimal number of bases...")
        best_solution = None
        best_score = float('-inf')
        
        # Track metrics for plotting
        metrics_history = {
            'optimal_coverage': [],
            'under_coverage': [],
            'over_coverage': [],
            'num_bases': []
        }
        
        # Start from 8 bases instead of 5, and use fewer iterations
        for num_bases in range(8, max_bases + 1):
            sites, _ = self.optimize_sites(num_bases, iterations=50)  # Reduced iterations
            
            # Get coverage statistics
            coverage_counts = self.grid.get_coverage_counts()
            zero_coverage = np.sum(coverage_counts == 0)
            
            # Calculate coverage metrics
            total_points = self.grid.grid_points ** 2
            optimal_coverage = np.sum(coverage_counts == 5) / total_points
            under_coverage = np.sum(coverage_counts < 5) / total_points
            over_coverage = np.sum(coverage_counts > 5) / total_points
            
            # Store metrics
            metrics_history['optimal_coverage'].append(optimal_coverage)
            metrics_history['under_coverage'].append(under_coverage)
            metrics_history['over_coverage'].append(over_coverage)
            metrics_history['num_bases'].append(num_bases)
            
            # Calculate intersection score - prioritize where under and over coverage lines meet
            intersection_score = -abs(under_coverage - over_coverage) * 1000
            coverage_score = (optimal_coverage * 1000 - 
                            abs(under_coverage - over_coverage) * 2000 -
                            num_bases * 25)
            
            print(f"\nConfiguration with {num_bases} bases:")
            print(f"Optimal coverage (5): {optimal_coverage:.1%}")
            print(f"Under coverage (<5): {under_coverage:.1%}")
            print(f"Over coverage (>5): {over_coverage:.1%}")
            print(f"Score: {coverage_score:.2f}")
            
            # Update best solution when lines are closest to crossing
            if coverage_score > best_score and zero_coverage == 0:
                best_score = coverage_score
                best_solution = {
                    'sites': sites,
                    'num_sites': num_bases,
                    'coverage': coverage_score,
                    'optimal_ratio': optimal_coverage,
                    'under_ratio': under_coverage,
                    'over_ratio': over_coverage
                }
                print(f"New best configuration found!")
                
                # If we've found a good intersection point, we can stop
                if abs(under_coverage - over_coverage) < 0.05:
                    print(f"Found optimal intersection at {num_bases} bases!")
                    break
        
        best_solution['metrics_history'] = metrics_history
        return best_solution

    def perturb_sites(self, sites: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Generate a new grid configuration rather than small movements"""
        num_sites = len(sites)
        
        # 50% chance to try a completely new configuration
        if np.random.random() < 0.5:
            return self.generate_initial_sites(num_sites)
        
        # Otherwise, make larger movements to existing sites
        new_sites = sites.copy()
        
        # Move 2-3 bases to new positions
        num_moves = np.random.randint(2, 4)
        for _ in range(num_moves):
            idx = np.random.randint(0, len(sites))
            
            # Generate new position relative to center
            center_x = self.grid.area_size_meters / 2
            center_y = self.grid.area_size_meters / 2
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0.3, 0.8) * self.grid.max_range
            
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            
            # Ensure within bounds
            x = np.clip(x, self.grid.max_range * 0.2, 
                       self.grid.area_size_meters - self.grid.max_range * 0.2)
            y = np.clip(y, self.grid.max_range * 0.2, 
                       self.grid.area_size_meters - self.grid.max_range * 0.2)
            
            new_sites[idx] = (x, y)
        
        return new_sites

    def calculate_score(self, coverage_counts: np.ndarray, num_sites: int) -> float:
        """Calculate score for current configuration"""
        zero_coverage = np.sum(coverage_counts == 0)
        
        # Immediately disqualify configurations with zero coverage
        if zero_coverage > 0:
            return float('-inf')
        
        # Target exactly 5 bases coverage
        target = 5
        
        # Calculate coverage distribution metrics
        under_coverage = np.sum(coverage_counts < target)
        over_coverage = np.sum(coverage_counts > target)
        optimal_coverage = np.sum(coverage_counts == target)
        
        # Calculate intersection penalty
        intersection_penalty = abs(under_coverage - over_coverage) * 2000
        
        # Calculate weighted score components
        optimal_bonus = optimal_coverage * 2500
        base_penalty = num_sites * 25
        
        # Calculate final score
        score = (optimal_bonus - 
                intersection_penalty - 
                base_penalty)
        
        return score