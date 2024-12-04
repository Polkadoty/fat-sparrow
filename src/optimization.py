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

    def generate_initial_sites(self, num_sites: int = 6) -> List[Tuple[float, float]]:
        """Generate initial launch sites with better coverage guarantee"""
        sites = []
        max_radius = min(self.grid.area_size_meters / 2.2,
                        self.grid.max_range * 1.1)
        center = (self.grid.area_size_meters / 2, self.grid.area_size_meters / 2)
        
        # First, ensure coverage of corners and edges
        edge_margin = self.grid.max_range * 0.15
        edge_positions = [
            (edge_margin, edge_margin),  # Bottom left
            (edge_margin, self.grid.area_size_meters - edge_margin),  # Top left
            (self.grid.area_size_meters - edge_margin, edge_margin),  # Bottom right
            (self.grid.area_size_meters - edge_margin, 
             self.grid.area_size_meters - edge_margin)  # Top right
        ]
        
        # Add corner bases if we have enough sites
        if num_sites >= 4:
            sites.extend(edge_positions[:min(4, num_sites)])
        
        # Add remaining sites using radial distribution
        remaining_sites = num_sites - len(sites)
        if remaining_sites > 0:
            angles = np.linspace(0, 2 * np.pi, remaining_sites, endpoint=False)
            np.random.shuffle(angles)
            
            for angle in angles:
                while True:
                    radius = np.random.uniform(0.3 * max_radius, max_radius)
                    prob = self.calculate_radial_probability(radius, max_radius)
                    if np.random.random() < prob:
                        break
                
                x = center[0] + radius * np.cos(angle)
                y = center[1] + radius * np.sin(angle)
                
                # Ensure within bounds
                margin = self.grid.max_range * 0.15
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

    def find_minimum_bases(self, max_bases: int = 24) -> dict:
        """Find minimum number of bases needed for optimal 4-point coverage"""
        print("\nSearching for optimal number of bases...")
        best_solution = None
        best_score = float('-inf')
        
        for num_bases in range(6, max_bases + 1):
            sites, _ = self.optimize_sites(num_bases, iterations=100)
            
            # Get coverage statistics
            coverage_counts = self.grid.get_coverage_counts()
            zero_coverage = np.sum(coverage_counts == 0)
            
            # Calculate coverage metrics
            optimal_coverage = np.sum(coverage_counts == 4)
            under_coverage = np.sum(coverage_counts < 4)
            over_coverage = np.sum(coverage_counts > 4)
            
            # Calculate efficiency score
            total_points = self.grid.grid_points ** 2
            optimal_ratio = optimal_coverage / total_points
            under_ratio = under_coverage / total_points
            over_ratio = over_coverage / total_points
            
            # Score prioritizes exactly 4 coverage
            score = (optimal_ratio * 1000 -           # Reward optimal coverage
                    under_ratio * 2500 -              # Heavily penalize under-coverage
                    over_ratio * 500 -                # Lightly penalize over-coverage
                    num_bases * 25)                   # Very small penalty for more bases
            
            print(f"\nConfiguration with {num_bases} bases:")
            print(f"Optimal coverage (4): {optimal_ratio:.1%}")
            print(f"Under coverage (<4): {under_ratio:.1%}")
            print(f"Over coverage (>4): {over_ratio:.1%}")
            print(f"Score: {score:.2f}")
            
            if score > best_score and zero_coverage == 0:
                best_score = score
                best_solution = {
                    'sites': sites,
                    'num_sites': num_bases,
                    'coverage': score,
                    'optimal_ratio': optimal_ratio,
                    'under_ratio': under_ratio,
                    'over_ratio': over_ratio
                }
                print(f"New best configuration found!")
        
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
        
        # Target exactly 4 bases coverage
        target = 4
        
        # Calculate coverage distribution metrics
        under_coverage = np.sum(coverage_counts < target)
        over_coverage = np.sum(coverage_counts > target)
        optimal_coverage = np.sum(coverage_counts == target)
        
        # Calculate weighted score components
        under_penalty = under_coverage * 2500      # Heavy penalty for under-coverage
        over_penalty = over_coverage * 500         # Lighter penalty for over-coverage
        optimal_bonus = optimal_coverage * 1000
        
        # Additional penalties for extreme under-coverage
        extreme_under = np.sum(coverage_counts < 3) * 4000
        
        # Calculate final score
        score = (optimal_bonus - 
                under_penalty - 
                over_penalty - 
                extreme_under)
        
        return score