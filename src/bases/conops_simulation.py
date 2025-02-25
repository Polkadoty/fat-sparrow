import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path
import matplotlib.colors as colors
from typing import List, Tuple, Dict
from dataclasses import dataclass
import random

@dataclass(frozen=True)  # Make the dataclass immutable and hashable
class Base:
    name: str
    position: Tuple[float, float]
    type: str  # 'MOB' or 'FOB'
    range_nm: float = 6.03

    def __hash__(self):
        return hash((self.name, self.position, self.type, self.range_nm))
    
    def __eq__(self, other):
        if not isinstance(other, Base):
            return NotImplemented
        return (self.name == other.name and 
                self.position == other.position and 
                self.type == other.type and 
                self.range_nm == other.range_nm)

@dataclass
class Aircraft:
    position: Tuple[float, float]
    heading: float
    base: Base
    state: str  # 'patrol', 'intercept', 'circle', 'rtb'
    patrol_points: List[Tuple[float, float]] = None
    patrol_index: int = 0
    fireballs_dropped: int = 0  # Add counter for fireballs
    last_fireball_time: float = 0  # Track time of last fireball drop

class ConOpsSimulation:
    def __init__(self):
        self.AREA_SIZE_NM = 17.07
        self.NM_TO_KM = 1.852
        self.AIRCRAFT_SPEED_KTS = 76  # Updated to 76 knots for payload aircraft
        self.PATROL_SPEED_KTS = 60    # Keep patrol speed at 60 knots
        self.TURN_RADIUS_NM = 0.5
        
        # Initialize bases
        center = self.AREA_SIZE_NM / 2
        offset = 5  # Distance from center to FOBs
        
        self.bases = [
            Base('MOB', (center, center), 'MOB'),
            Base('FOB 1', (center + offset, center + offset), 'FOB'),
            Base('FOB 2', (center + offset, center - offset), 'FOB'),
            Base('FOB 3', (center - offset, center - offset), 'FOB'),
            Base('FOB 4', (center - offset, center + offset), 'FOB')
        ]
        
        # Initialize aircraft at bases
        self.aircraft = []
        self.setup_patrol_routes()
        
        # Simulation state
        self.fire_location = None
        self.elapsed_time = 0
        self.phase = 'patrol'  # patrol, response, mass_response
        
    def generate_patrol_route(self) -> List[Tuple[float, float]]:
        """
        Generate a rectangular racetrack search pattern, traversed clockwise.

        The route goes:
          - Up along the left edge,
          - Right along the top edge,
          - Down along the right edge,
          - Left along the bottom edge.
        """
        # Define boundaries (you can adjust these as needed)
        left_x = 1.67
        right_x = 5.93
        bottom_y = 2
        top_y = 14.7
        num_points = 50  # points along each edge for smoothness

        route_points = []
        # Left edge (from bottom to top) – flying north
        for y in np.linspace(bottom_y, top_y, num_points):
            route_points.append((left_x, y))
        # Top edge (from left to right) – flying east
        for x in np.linspace(left_x, right_x, num_points):
            route_points.append((x, top_y))
        # Right edge (from top to bottom) – flying south
        for y in np.linspace(top_y, bottom_y, num_points):
            route_points.append((right_x, y))
        # Bottom edge (from right to left) – flying west
        for x in np.linspace(right_x, left_x, num_points):
            route_points.append((x, bottom_y))

        return route_points

    def generate_rounded_racetrack_route(self, center: Tuple[float, float], width: float, height: float, 
                                           corner_radius: float, p_straight: int = 20, p_arc: int = 10) -> List[Tuple[float, float]]:
        """
        Generate a rounded racetrack route (rounded rectangle) in clockwise order.

        The rounded rectangle is built from four straight segments and four quarter-circle arcs.
        The order of segments is:
          1. Top edge (left to right)
          2. Top-right corner (arc from 90° to 0°)
          3. Right edge (top to bottom)
          4. Bottom-right corner (arc from 0° to -90°)
          5. Bottom edge (right to left)
          6. Bottom-left corner (arc from -90° to -180°)
          7. Left edge (bottom to top)
          8. Top-left corner (arc from 180° to 90°)

        :param center: Center of the rectangle (x, y).
        :param width: Total width of the rectangle.
        :param height: Total height of the rectangle.
        :param corner_radius: Radius for rounding the corners.
        :param p_straight: Number of points for each straight segment.
        :param p_arc: Number of points for each arc segment.
        :return: List of (x, y) points representing the route.
        """
        cx, cy = center
        x_min = cx - width / 2
        x_max = cx + width / 2
        y_min = cy - height / 2
        y_max = cy + height / 2
        r = corner_radius

        route = []

        # 1. Top edge: from (x_min + r, y_max) to (x_max - r, y_max)
        top_edge = [(x, y_max) for x in np.linspace(x_min + r, x_max - r, p_straight)]
        route.extend(top_edge)

        # 2. Top-right corner: arc with center at (x_max - r, y_max - r)
        center_tr = (x_max - r, y_max - r)
        angles_tr = np.linspace(np.pi/2, 0, p_arc, endpoint=False)
        arc_tr = [(center_tr[0] + r * np.cos(theta), center_tr[1] + r * np.sin(theta)) for theta in angles_tr]
        route.extend(arc_tr)

        # 3. Right edge: from (x_max, y_max - r) down to (x_max, y_min + r)
        right_edge = [(x_max, y) for y in np.linspace(y_max - r, y_min + r, p_straight)]
        route.extend(right_edge)

        # 4. Bottom-right corner: arc with center at (x_max - r, y_min + r)
        center_br = (x_max - r, y_min + r)
        angles_br = np.linspace(0, -np.pi/2, p_arc, endpoint=False)
        arc_br = [(center_br[0] + r * np.cos(theta), center_br[1] + r * np.sin(theta)) for theta in angles_br]
        route.extend(arc_br)

        # 5. Bottom edge: from (x_max - r, y_min) to (x_min + r, y_min)
        bottom_edge = [(x, y_min) for x in np.linspace(x_max - r, x_min + r, p_straight)]
        route.extend(bottom_edge)

        # 6. Bottom-left corner: arc with center at (x_min + r, y_min + r)
        center_bl = (x_min + r, y_min + r)
        angles_bl = np.linspace(-np.pi/2, -np.pi, p_arc, endpoint=False)
        arc_bl = [(center_bl[0] + r * np.cos(theta), center_bl[1] + r * np.sin(theta)) for theta in angles_bl]
        route.extend(arc_bl)

        # 7. Left edge: from (x_min, y_min + r) up to (x_min, y_max - r)
        left_edge = [(x_min, y) for y in np.linspace(y_min + r, y_max - r, p_straight)]
        route.extend(left_edge)

        # 8. Top-left corner: arc with center at (x_min + r, y_max - r)
        center_tl = (x_min + r, y_max - r)
        angles_tl = np.linspace(np.pi, np.pi/2, p_arc, endpoint=False)
        arc_tl = [(center_tl[0] + r * np.cos(theta), center_tl[1] + r * np.sin(theta)) for theta in angles_tl]
        route.extend(arc_tl)

        return route

    def get_evenly_spaced_points(self, route: List[Tuple[float, float]], num_points: int) -> List[Tuple[float, float]]:
        """
        Given a route (list of (x,y) points forming a closed loop), re-sample and return `num_points`
        uniformly spaced along the entire perimeter.
        """
        # Ensure the route is a closed loop.
        if route[0] != route[-1]:
            closed_route = route + [route[0]]
        else:
            closed_route = route

        # Compute cumulative distances along the closed route.
        cum_dist = [0.0]
        for i in range(1, len(closed_route)):
            dx = closed_route[i][0] - closed_route[i - 1][0]
            dy = closed_route[i][1] - closed_route[i - 1][1]
            cum_dist.append(cum_dist[-1] + np.hypot(dx, dy))
        total_length = cum_dist[-1]
        spacing = total_length / num_points

        uniform_points = []
        seg = 0
        for i in range(num_points):
            target = i * spacing
            # Advance the segment until the target is less than the next cumulative distance.
            while seg < len(cum_dist) - 1 and cum_dist[seg + 1] < target:
                seg += 1
            # Linear interpolation for the target point.
            seg_length = cum_dist[seg + 1] - cum_dist[seg]
            if seg_length == 0:
                t = 0
            else:
                t = (target - cum_dist[seg]) / seg_length
            x = closed_route[seg][0] + t * (closed_route[seg + 1][0] - closed_route[seg][0])
            y = closed_route[seg][1] + t * (closed_route[seg + 1][1] - closed_route[seg][1])
            uniform_points.append((x, y))
        return uniform_points

    def find_nearest_index(self, route: List[Tuple[float, float]], point: Tuple[float, float]) -> int:
        """
        Return the index of the point in `route` that is closest to the given `point`.
        """
        best_idx = 0
        best_dist = float('inf')
        for i, pt in enumerate(route):
            dist = self.calculate_distance(pt, point)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        return best_idx

    def setup_patrol_routes(self):
        """
        Create two patrol routes for search aircraft using rounded racetrack patterns.
        Left route is centered on FOBs 3 & 4 while right route is centered on FOBs 1 & 2.
        Each route is assigned 8 aircraft (total of 16).
        The aircraft starting positions are evenly spaced along the route,
        and their heading is initialized based on the direction toward the next evenly
        spaced point.
        """
        self.aircraft = []
        num_aircraft_per_route = 8

        # Overall simulation center and offset from the __init__ parameters.
        sim_center = self.AREA_SIZE_NM / 2  # e.g., 8.535 if AREA_SIZE_NM is 17.07
        offset = 5  # Distance from center to FOBs (as defined in __init__)

        # Define centers for the two racetracks based on the FOB clusters.
        # For the left route (FOB 3 & FOB 4) and right route (FOB 1 & FOB 2).
        left_center = (sim_center - offset, sim_center)
        right_center = (sim_center + offset, sim_center)

        # Use the old patrol dimensions (4.27 nm wide, 14 nm tall) as desired.
        route_width = 4.27   # 4.27 nm wide
        route_height = 14.0  # 14 nm tall
        corner_radius = 0.5

        left_route = self.generate_rounded_racetrack_route(left_center, route_width, route_height, corner_radius)
        right_route = self.generate_rounded_racetrack_route(right_center, route_width, route_height, corner_radius)

        # Determine the FOBs for each route.
        left_fobs = [base for base in self.bases if base.name in ['FOB 3', 'FOB 4']]
        right_fobs = [base for base in self.bases if base.name in ['FOB 1', 'FOB 2']]

        # Get 8 evenly spaced starting positions along the full perimeter for each route.
        uniform_left_points = self.get_evenly_spaced_points(left_route, num_aircraft_per_route)
        uniform_right_points = self.get_evenly_spaced_points(right_route, num_aircraft_per_route)

        # Initialize aircraft for the left route.
        for i, pos in enumerate(uniform_left_points):
            # For robust heading determination, find the nearest index in the detailed route.
            patrol_index = self.find_nearest_index(left_route, pos)
            # Next target: use the next point in the detailed route (cyclically).
            next_index = (patrol_index + 1) % len(left_route)
            dx = left_route[next_index][0] - left_route[patrol_index][0]
            dy = left_route[next_index][1] - left_route[patrol_index][1]
            heading = np.arctan2(dy, dx)
            base = left_fobs[i % len(left_fobs)]
            self.aircraft.append(Aircraft(
                position=pos,
                heading=heading,
                base=base,
                state='patrol',
                patrol_points=left_route,
                patrol_index=patrol_index
            ))

        # Initialize aircraft for the right route.
        for i, pos in enumerate(uniform_right_points):
            patrol_index = self.find_nearest_index(right_route, pos)
            next_index = (patrol_index + 1) % len(right_route)
            dx = right_route[next_index][0] - right_route[patrol_index][0]
            dy = right_route[next_index][1] - right_route[patrol_index][1]
            heading = np.arctan2(dy, dx)
            base = right_fobs[i % len(right_fobs)]
            self.aircraft.append(Aircraft(
                position=pos,
                heading=heading,
                base=base,
                state='patrol',
                patrol_points=right_route,
                patrol_index=patrol_index
            ))

    def generate_fire(self):
        """Generate random fire location near center of area"""
        center = self.AREA_SIZE_NM / 2
        radius = 5.0  # 5 NM radius from center
        
        # Generate random angle and distance within radius
        angle = random.uniform(0, 2 * np.pi)
        distance = random.uniform(0, radius)
        
        # Convert to cartesian coordinates
        x = center + distance * np.cos(angle)
        y = center + distance * np.sin(angle)
        
        self.fire_location = (x, y)
        self.phase = 'response'
        self.elapsed_time = 0  # Reset clock when fire starts
        
        # Store the first responder for reference
        closest_aircraft = min(self.aircraft, 
                             key=lambda a: self.calculate_distance(a.position, self.fire_location))
        closest_aircraft.state = 'intercept'
        self.first_responder = closest_aircraft

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate straight-line distance between two points"""
        return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

    def update_aircraft(self, dt: float):
        """
        Update aircraft positions and states.
        (For brevity, only the revised patrol branch is shown here.)
        """
        for aircraft in self.aircraft:
            if aircraft.state == 'patrol':
                # Follow the patrol (racetrack) route in order
                target = aircraft.patrol_points[aircraft.patrol_index]
                if self.calculate_distance(aircraft.position, target) < 0.05:
                    # Once close enough, increment to the next point (wrap around)
                    aircraft.patrol_index = (aircraft.patrol_index + 1) % len(aircraft.patrol_points)
                    target = aircraft.patrol_points[aircraft.patrol_index]

                # Compute heading and move towards the target
                dx = target[0] - aircraft.position[0]
                dy = target[1] - aircraft.position[1]
                heading = np.arctan2(dy, dx)
                speed = self.PATROL_SPEED_KTS * dt / 3600.0  # Convert knots to NM per dt
                aircraft.position = (
                    aircraft.position[0] + speed * np.cos(heading),
                    aircraft.position[1] + speed * np.sin(heading)
                )
                aircraft.heading = heading

            elif aircraft.state == 'intercept':
                # Move towards fire
                dx = self.fire_location[0] - aircraft.position[0]
                dy = self.fire_location[1] - aircraft.position[1]
                dist = np.sqrt(dx**2 + dy**2)
                
                if dist < self.TURN_RADIUS_NM:
                    aircraft.state = 'circle'
                else:
                    heading = np.arctan2(dy, dx)
                    speed = self.AIRCRAFT_SPEED_KTS * dt / 3600
                    
                    aircraft.position = (
                        aircraft.position[0] + speed * np.cos(heading),
                        aircraft.position[1] + speed * np.sin(heading)
                    )
                    aircraft.heading = heading
                    
            elif aircraft.state == 'circle':
                # Track time spent circling
                if not hasattr(aircraft, 'circle_time'):
                    aircraft.circle_time = 0
                aircraft.circle_time += dt
                
                # Update fireball counter for non-first responders
                if aircraft != self.first_responder:
                    # Check if 30 seconds have passed since last fireball drop
                    if self.elapsed_time - aircraft.last_fireball_time >= 30:
                        aircraft.fireballs_dropped += 3
                        aircraft.last_fireball_time = self.elapsed_time
                
                # First responder circles indefinitely, others return after 2 minutes
                if (aircraft.circle_time >= 120 and  # 2 minutes
                    aircraft != self.first_responder):
                    aircraft.state = 'rtb'
                    continue
                
                # Continue with normal circle behavior
                angle = np.arctan2(aircraft.position[1] - self.fire_location[1],
                                 aircraft.position[0] - self.fire_location[0])
                angle += (self.AIRCRAFT_SPEED_KTS * dt / 3600) / self.TURN_RADIUS_NM
                
                aircraft.position = (
                    self.fire_location[0] + self.TURN_RADIUS_NM * np.cos(angle),
                    self.fire_location[1] + self.TURN_RADIUS_NM * np.sin(angle)
                )
                aircraft.heading = angle + np.pi/2
            
            elif aircraft.state == 'rtb':
                # Return to base
                dx = aircraft.base.position[0] - aircraft.position[0]
                dy = aircraft.base.position[1] - aircraft.position[1]
                dist = np.sqrt(dx**2 + dy**2)
                
                if dist < 0.1:  # If close to base, remove aircraft
                    self.aircraft.remove(aircraft)
                else:
                    heading = np.arctan2(dy, dx)
                    speed = self.AIRCRAFT_SPEED_KTS * dt / 3600
                    
                    aircraft.position = (
                        aircraft.position[0] + speed * np.cos(heading),
                        aircraft.position[1] + speed * np.sin(heading)
                    )
                    aircraft.heading = heading

    def launch_mass_response(self):
        """Launch first wave of aircraft from all FOBs"""
        self.response_launches = 1  # First wave
        self.next_launch_time = self.elapsed_time + 60  # Next wave in 60 seconds
        
        # Launch one aircraft from each FOB immediately
        for base in self.bases[1:]:  # Skip MOB
            self.aircraft.append(Aircraft(
                position=base.position,
                heading=0,
                base=base,
                state='intercept'
            ))

    def update_mass_response(self):
        """Update mass response launches"""
        if (self.phase == 'mass_response' and 
            self.response_launches < 4 and 
            self.elapsed_time >= self.next_launch_time):
            
            # Launch one aircraft from each FOB
            for base in self.bases[1:]:  # Skip MOB
                self.aircraft.append(Aircraft(
                    position=base.position,
                    heading=0,
                    base=base,
                    state='intercept'
                ))
            
            self.response_launches += 1
            self.next_launch_time += 60  # Next wave in 60 seconds

    def animate(self, frame_num: int):
        """Animation update function"""
        # Clear previous figure to prevent memory issues
        plt.clf()
        
        # Initial patrol period (5 seconds * 15 fps = 75 frames)
        if frame_num < 75:  # First 5 seconds
            dt = 1.0  # Keep aircraft moving during initial patrol
            if frame_num == 74:  # Last frame of initial patrol
                self.generate_fire()
        else:
            # Convert frame time to simulation time
            dt = 1.6  # 600/(25*15) seconds of simulation time per frame
            
        # Update simulation time if not in final pause
        if frame_num < 450:  # 75 + (25*15) = 450 frames for main simulation
            self.elapsed_time += dt
            
            # Mass response at 2.5 minutes (150 seconds)
            if self.phase == 'response' and self.elapsed_time >= 150:
                self.phase = 'mass_response'
                self.launch_mass_response()
            
            # Update staggered launches
            self.update_mass_response()
            
            # Update aircraft positions
            self.update_aircraft(dt)
        
        # Draw current state
        self.draw_current_state()

    def draw_current_state(self):
        """Draw the current state of the simulation"""
        plt.xlim(0, self.AREA_SIZE_NM)
        plt.ylim(0, self.AREA_SIZE_NM)
        plt.grid(True)

        # Draw the two patrol routes as dashed lines.
        # Use the same parameters as in setup_patrol_routes:
        sim_center = self.AREA_SIZE_NM / 2
        offset = 5  # same as in setup_patrol_routes
        route_width = 4.27   # 4.27 nm wide
        route_height = 14.0  # 14 nm tall
        corner_radius = 0.5

        left_center = (sim_center - offset, sim_center)
        right_center = (sim_center + offset, sim_center)
        left_route = self.generate_rounded_racetrack_route(left_center, route_width, route_height, corner_radius)
        right_route = self.generate_rounded_racetrack_route(right_center, route_width, route_height, corner_radius)
        left_x, left_y = zip(*left_route)
        right_x, right_y = zip(*right_route)
        plt.plot(left_x, left_y, 'k--', alpha=0.3)  # Dashed line for left route
        plt.plot(right_x, right_y, 'k--', alpha=0.3)  # Dashed line for right route

        # Draw bases (without range circles)
        for base in self.bases:
            plt.plot(base.position[0], base.position[1],
                     'bs' if base.type == 'MOB' else 'gs', markersize=10)

        # Draw fire location if it exists
        if self.fire_location:
            plt.plot(self.fire_location[0], self.fire_location[1], 'rx', markersize=15)

        # Draw aircraft
        for aircraft in self.aircraft:
            color = {
                'patrol': 'blue',
                'intercept': 'red',
                'circle': 'orange',
                'rtb': 'gray'
            }.get(aircraft.state, 'black')
            plt.plot(aircraft.position[0], aircraft.position[1],
                     'o', color=color, markersize=6)

            # Draw heading indicator
            heading_length = 0.5
            dx = heading_length * np.cos(aircraft.heading)
            dy = heading_length * np.sin(aircraft.heading)
            plt.arrow(aircraft.position[0], aircraft.position[1], dx, dy,
                      head_width=0.2, head_length=0.3, fc=color, ec=color)

        # Show timer and fireball count after fire starts
        if self.fire_location:
            minutes = int(self.elapsed_time // 60)
            seconds = int(self.elapsed_time % 60)
            total_fireballs = sum(aircraft.fireballs_dropped for aircraft in self.aircraft)
            plt.title(f'Mission Time: {minutes:02d}:{seconds:02d} | Total Fireballs: {total_fireballs}')
        else:
            plt.title('Initial Patrol')

        plt.xlabel('Distance (NM)')
        plt.ylabel('Distance (NM)')

def run_simulation():
    """Run the simulation and save as gif"""
    sim = ConOpsSimulation()
    
    # Calculate total frames:
    # 5 seconds initial + 25 seconds simulation + 5 seconds pause = 35 seconds
    # At 15 fps = 525 total frames
    total_frames = 35 * 15
    
    # Create figure
    fig = plt.figure(figsize=(10, 10))
    
    # Create animation
    anim = FuncAnimation(
        fig, 
        sim.animate,
        frames=total_frames,
        interval=1000/15,  # 15 fps
        repeat=False
    )
    
    # Save animation
    anim.save('conops_simulation.gif', 
              writer='pillow', 
              fps=15)
    
    # Close figure to prevent memory warning
    plt.close()

if __name__ == "__main__":
    run_simulation() 