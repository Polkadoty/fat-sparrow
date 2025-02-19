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
        
    def setup_patrol_routes(self):
        """Create patrol routes for both sides simultaneously"""
        left_patrol = self.generate_patrol_route(True)   # Left side patrol
        right_patrol = self.generate_patrol_route(False) # Right side patrol
        
        # Create 8 aircraft for each patrol route, evenly spaced
        self.aircraft = []
        for i in range(8):
            # Left patrol aircraft (clockwise)
            start_index = (i * len(left_patrol) // 8) % len(left_patrol)
            points_per_side = len(left_patrol) // 4
            section = (start_index // points_per_side) % 4  # 0=left, 1=top, 2=right, 3=bottom
            heading = {
                0: np.pi/2,    # left side: going up
                1: 0,          # top: going right
                2: -np.pi/2,   # right side: going down
                3: np.pi       # bottom: going left
            }[section]
            
            self.aircraft.append(Aircraft(
                position=left_patrol[start_index],
                heading=heading,
                base=self.bases[1],
                state='patrol',
                patrol_points=left_patrol,
                patrol_index=start_index
            ))
            
            # Right patrol aircraft (counterclockwise)
            start_index = (i * len(right_patrol) // 8) % len(right_patrol)
            section = (start_index // points_per_side) % 4
            # Different heading map for right patrol
            heading = {
                0: -np.pi/2,   # left side: going down
                1: 0,          # top: going right
                2: np.pi/2,    # right side: going up
                3: np.pi       # bottom: going left
            }[section]
            
            self.aircraft.append(Aircraft(
                position=right_patrol[start_index],
                heading=heading,
                base=self.bases[2],
                state='patrol',
                patrol_points=right_patrol,
                patrol_index=start_index
            ))

    def generate_patrol_route(self, is_left_route: bool) -> List[Tuple[float, float]]:
        """Generate vertical patrol route with specified direction"""
        if is_left_route:
            # Left patrol route coordinates (clockwise)
            left_line_x = 1.67
            right_line_x = 5.93
        else:
            # Right patrol route coordinates (counterclockwise)
            left_line_x = 11.14    # 17.07 - 5.93
            right_line_x = 15.4    # 17.07 - 1.67
        
        y_bottom = 2
        y_top = 14.7
        r = self.TURN_RADIUS_NM
        
        # Create route points based on direction
        route_points = []
        
        if is_left_route:
            # Left vertical line (going up)
            for y in np.linspace(y_bottom + r, y_top - r, 40):
                route_points.append((left_line_x, y))
            
            # Top-left corner
            for angle in np.linspace(-np.pi/2, 0, 20):
                x = left_line_x + r * np.cos(angle)
                y = y_top - r + r * np.sin(angle)
                route_points.append((x, y))
            
            # Top horizontal line
            for x in np.linspace(left_line_x + r, right_line_x - r, 40):
                route_points.append((x, y_top))
            
            # Top-right corner
            for angle in np.linspace(0, np.pi/2, 20):
                x = right_line_x - r + r * np.cos(angle)
                y = y_top - r + r * np.sin(angle)
                route_points.append((x, y))
            
            # Right vertical line (going down)
            for y in np.linspace(y_top - r, y_bottom + r, 40)[::-1]:
                route_points.append((right_line_x, y))
            
            # Bottom-right corner
            for angle in np.linspace(np.pi/2, np.pi, 20):
                x = right_line_x - r + r * np.cos(angle)
                y = y_bottom + r + r * np.sin(angle)
                route_points.append((x, y))
            
            # Bottom horizontal line
            for x in np.linspace(right_line_x - r, left_line_x + r, 40)[::-1]:
                route_points.append((x, y_bottom))
            
            # Bottom-left corner
            for angle in np.linspace(np.pi, 3*np.pi/2, 20):
                x = left_line_x + r + r * np.cos(angle)
                y = y_bottom + r + r * np.sin(angle)
                route_points.append((x, y))
            
        else:
            # Left vertical line (going down)
            for y in np.linspace(y_top - r, y_bottom + r, 40)[::-1]:
                route_points.append((left_line_x, y))
            
            # Bottom-left corner
            for angle in np.linspace(-np.pi/2, 0, 20):
                x = left_line_x + r * np.cos(angle)
                y = y_bottom + r + r * np.sin(angle)
                route_points.append((x, y))
            
            # Bottom horizontal line
            for x in np.linspace(left_line_x + r, right_line_x - r, 40):
                route_points.append((x, y_bottom))
            
            # Bottom-right corner
            for angle in np.linspace(0, np.pi/2, 20):
                x = right_line_x - r + r * np.cos(angle)
                y = y_bottom + r + r * np.sin(angle)
                route_points.append((x, y))
            
            # Right vertical line (going up)
            for y in np.linspace(y_bottom + r, y_top - r, 40):
                route_points.append((right_line_x, y))
            
            # Top-right corner
            for angle in np.linspace(np.pi/2, np.pi, 20):
                x = right_line_x - r + r * np.cos(angle)
                y = y_top - r + r * np.sin(angle)
                route_points.append((x, y))
            
            # Top horizontal line
            for x in np.linspace(right_line_x - r, left_line_x + r, 40)[::-1]:
                route_points.append((x, y_top))
            
            # Top-left corner
            for angle in np.linspace(np.pi, 3*np.pi/2, 20):
                x = left_line_x + r + r * np.cos(angle)
                y = y_top - r + r * np.sin(angle)
                route_points.append((x, y))
        
        return route_points

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
        """Update aircraft positions and states"""
        for aircraft in self.aircraft:
            if aircraft.state == 'patrol':
                # Move to next patrol point with smoother motion
                target = aircraft.patrol_points[aircraft.patrol_index]
                dist = self.calculate_distance(aircraft.position, target)
                
                if dist < 0.05:  # Reduced threshold for smoother transitions
                    # Simply increment index for all aircraft
                    aircraft.patrol_index = (aircraft.patrol_index + 1) % len(aircraft.patrol_points)
                
                # Move towards target
                dx = target[0] - aircraft.position[0]
                dy = target[1] - aircraft.position[1]
                heading = np.arctan2(dy, dx)
                speed = self.PATROL_SPEED_KTS * dt / 3600  # Convert to NM per timestep
                
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
        # Set up the plot
        plt.xlim(0, self.AREA_SIZE_NM)
        plt.ylim(0, self.AREA_SIZE_NM)
        plt.grid(True)
        
        # Draw patrol routes first (so they appear behind everything)
        left_route = self.generate_patrol_route(True)
        right_route = self.generate_patrol_route(False)
        
        # Draw both patrol routes
        left_x, left_y = zip(*left_route)
        right_x, right_y = zip(*right_route)
        plt.plot(left_x, left_y, 'k--', alpha=0.3)  # Black dotted line with transparency
        plt.plot(right_x, right_y, 'k--', alpha=0.3)  # Black dotted line with transparency
        
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
        
        # Only show timer and fireball count after fire starts
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