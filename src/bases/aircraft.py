import numpy as np
from typing import Tuple, List
from dataclasses import dataclass

@dataclass
class AircraftState:
    position: Tuple[float, float]  # (x, y) in meters
    heading: float  # in radians
    speed: float   # in m/s
    bank_angle: float  # in radians

class Aircraft:
    def __init__(self, 
                 initial_position: Tuple[float, float],
                 initial_heading: float = 0):
        # Constants
        self.MAX_BANK_ANGLE = np.radians(30)  # 30 degrees max bank
        self.BANK_RATE = np.radians(15)       # 15 degrees per second
        self.MAX_G_FORCE = 2.0                # Maximum g-force in turns
        self.NM_TO_METERS = 1852              # Conversion factor
        
        # Initial state
        self.state = AircraftState(
            position=initial_position,
            heading=initial_heading,
            speed=0,
            bank_angle=0
        )
        
        # Flight path history for visualization
        self.path_history: List[Tuple[float, float]] = [initial_position]

    def update(self, dt: float, target_heading: float, target_speed_knots: float):
        """
        Update aircraft state for one time step
        
        Args:
            dt: Time step in seconds
            target_heading: Desired heading in radians
            target_speed_knots: Desired speed in knots
        """
        # Convert target speed to m/s
        target_speed = target_speed_knots * self.NM_TO_METERS / 3600
        
        # Update speed (simple acceleration model)
        speed_diff = target_speed - self.state.speed
        acceleration = np.clip(speed_diff, -5, 5)  # 5 m/s^2 max acceleration
        self.state.speed += acceleration * dt
        
        # Calculate desired heading change
        heading_diff = self.normalize_angle(target_heading - self.state.heading)
        
        # Update bank angle
        if abs(heading_diff) > 0.01:  # If we need to turn
            target_bank = np.clip(heading_diff, -self.MAX_BANK_ANGLE, self.MAX_BANK_ANGLE)
            bank_diff = target_bank - self.state.bank_angle
            bank_change = np.clip(bank_diff, -self.BANK_RATE * dt, self.BANK_RATE * dt)
            self.state.bank_angle += bank_change
        else:
            # Return to level flight
            self.state.bank_angle = np.clip(self.state.bank_angle * 0.9, -0.01, 0.01)
        
        # Calculate turn rate based on bank angle and speed
        if self.state.speed > 0:
            # Turn radius = v^2 / (g * tan(bank_angle))
            g = 9.81  # m/s^2
            turn_rate = (g * np.tan(self.state.bank_angle) / 
                        max(self.state.speed, 1))  # radians per second
            self.state.heading += turn_rate * dt
        
        # Normalize heading to [-π, π]
        self.state.heading = self.normalize_angle(self.state.heading)
        
        # Update position
        dx = self.state.speed * np.cos(self.state.heading) * dt
        dy = self.state.speed * np.sin(self.state.heading) * dt
        new_position = (
            self.state.position[0] + dx,
            self.state.position[1] + dy
        )
        self.state.position = new_position
        self.path_history.append(new_position)

    def get_turn_radius(self, speed_knots: float) -> float:
        """Calculate minimum turn radius in meters at given speed"""
        speed_mps = speed_knots * self.NM_TO_METERS / 3600
        g = 9.81  # m/s^2
        return (speed_mps ** 2) / (g * np.tan(self.MAX_BANK_ANGLE))

    @staticmethod
    def normalize_angle(angle: float) -> float:
        """Normalize angle to [-π, π]"""
        return ((angle + np.pi) % (2 * np.pi)) - np.pi

    def calculate_intercept_course(self, target: Tuple[float, float]) -> float:
        """Calculate heading needed to intercept target"""
        dx = target[0] - self.state.position[0]
        dy = target[1] - self.state.position[1]
        return np.arctan2(dy, dx)

    def distance_to_target(self, target: Tuple[float, float]) -> float:
        """Calculate straight-line distance to target in meters"""
        dx = target[0] - self.state.position[0]
        dy = target[1] - self.state.position[1]
        return np.sqrt(dx**2 + dy**2) 