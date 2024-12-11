import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import os

# Constants
PAYLOAD_DIAMETER = 4.5 / 12  # 4.5 inches to feet
SHAFT_DIAMETER = 1 / 12  # 1 inch to feet
FUSELAGE_DIAMETER = 1.2  # Increased from 0.95 to 1.2 feet
ROTATION_TIME = 4  # seconds per rotation
FPS = 10  # 10 frames per second
ANIMATION_SPEEDUP = 2  # 2x speedup for the animation
TOTAL_FRAMES = ROTATION_TIME * FPS
DROP_SPEED = 1.5  # feet per second
DROP_TIME = 2  # seconds for payload drop
DROP_INTERVAL = 9  # seconds between drops
GRAVITY = 32.2  # feet per second squared
ACTUAL_DROP_TIME = 1.0  # seconds for actual dropping motion
DROP_MARGIN = 0.5  # seconds before and after drop
PAYLOAD_RADIUS = (4.5/12) / 2  # Convert 4.5 inches to feet radius
PAYLOAD_OFFSET = FUSELAGE_DIAMETER/2 - 0.2  # Adjusted offset for larger fuselage

# Initialize the plot
fig, ax = plt.subplots()
def init_plot():
    ax.set_xlim(-FUSELAGE_DIAMETER, FUSELAGE_DIAMETER)
    ax.set_ylim(-FUSELAGE_DIAMETER - 1.0, FUSELAGE_DIAMETER)
    ax.set_aspect('equal')
    ax.axis('off')

def draw_gravity_arrow():
    # Draw gravity arrow
    arrow_start = (FUSELAGE_DIAMETER * 0.8, FUSELAGE_DIAMETER * 0.8)
    arrow_length = FUSELAGE_DIAMETER * 0.3
    plt.arrow(arrow_start[0], arrow_start[1], 
             0, -arrow_length,
             head_width=0.05, head_length=0.1, 
             fc='black', ec='black')
    plt.text(arrow_start[0] + 0.1, arrow_start[1] - arrow_length/2, 'g', 
             fontsize=12, ha='left', va='center')

def draw_fuselage():
    # Draw the fuselage (purple, unmoving)
    fuselage = plt.Circle((0, 0), FUSELAGE_DIAMETER / 2, color='purple', fill=False, linewidth=2)
    ax.add_artist(fuselage)

    # Draw the shaft (red, unmoving)
    shaft = plt.Circle((0, 0), SHAFT_DIAMETER / 2, color='red', fill=True)
    ax.add_artist(shaft)

def draw_launcher(angle, empty_slots, drop_payload_data):
    # Draw the rotary launcher (blue, rotating)
    launcher = plt.Circle((0, 0), FUSELAGE_DIAMETER/2 - 0.1, color='blue', fill=True, alpha=0.6)
    ax.add_artist(launcher)

    # Draw the payload slots
    num_slots = 4
    angles = np.linspace(-np.pi/2, 3*np.pi/2, num_slots, endpoint=False)  # Start from bottom
    for i, slot_angle in enumerate(angles):
        x = PAYLOAD_OFFSET * np.cos(slot_angle + angle)
        y = PAYLOAD_OFFSET * np.sin(slot_angle + angle)

        if i in empty_slots:
            # Empty slot
            payload = plt.Circle((x, y), PAYLOAD_RADIUS, color='white', fill=True)
            ax.add_artist(payload)
        else:
            # Filled payload
            payload = plt.Circle((x, y), PAYLOAD_RADIUS, color='orange', fill=True)
            ax.add_artist(payload)

    # Draw falling payload if exists
    if drop_payload_data:
        x, y = drop_payload_data
        payload = plt.Circle((x, y), PAYLOAD_RADIUS, color='orange', fill=True)
        ax.add_artist(payload)

# Animation update function
def update(frame):
    ax.clear()
    init_plot()
    draw_fuselage()
    draw_gravity_arrow()

    time = (frame / FPS) * ANIMATION_SPEEDUP  # Adjust time for speedup
    cycle = int(time // DROP_INTERVAL)
    phase_time = time % DROP_INTERVAL

    # Initialize position variables
    empty_slots = set()
    drop_payload_data = None

    # Calculate base rotation from completed cycles
    if cycle == 0:
        rotation_angle = 0
    elif cycle == 1:
        rotation_angle = np.pi
    elif cycle == 2:
        rotation_angle = 3*np.pi/2
    elif cycle == 3:
        rotation_angle = 5*np.pi/2
    else:  # Reset animation after all payloads dropped
        if phase_time < 1.0:  # 1 second delay before reset
            empty_slots = {0, 1, 2, 3}
            rotation_angle = 5*np.pi/2
        else:
            empty_slots = set()
            rotation_angle = 0
        draw_launcher(rotation_angle, empty_slots, None)
        return

    # Set empty slots based on completed cycles
    if cycle >= 1:
        empty_slots.add(2)  # After first cycle: top empty
    if cycle >= 2:
        empty_slots.update({0, 2})  # After second cycle: top and bottom empty
    if cycle >= 3:
        empty_slots.update({0, 1, 3})  # After third cycle: all but top empty

    # Handle current cycle
    if phase_time <= (DROP_MARGIN + ACTUAL_DROP_TIME):
        # Active dropping phase
        if phase_time >= DROP_MARGIN:
            drop_time = phase_time - DROP_MARGIN
            falling_distance = 0.5 * GRAVITY * (drop_time ** 2)
            drop_payload_data = (0, -FUSELAGE_DIAMETER/2 - falling_distance)
            if drop_time > 0:
                if cycle == 0:
                    empty_slots.add(0)  # Clear bottom after first drop
                elif cycle == 1:
                    empty_slots.add(0)  # Clear bottom after second drop
                elif cycle == 2:
                    empty_slots = {0, 1, 3}  # Keep only top payload (slot 2)
                elif cycle == 3:
                    empty_slots.update({0, 1, 2, 3})  # Clear all after final drop
    else:
        # Rotation phase
        rotation_time = phase_time - DROP_TIME
        
        if cycle == 0:
            empty_slots.add(0)
            rotation_progress = min(1, rotation_time / 2)
            rotation_angle = rotation_progress * np.pi
        elif cycle == 1:
            empty_slots.update({0, 2})
            rotation_progress = min(1, rotation_time / 1)
            rotation_angle = np.pi + (rotation_progress * np.pi/2)
        elif cycle == 2:
            empty_slots = {0, 1, 3}  # Keep only top payload
            rotation_progress = min(1, rotation_time / 2)
            rotation_angle = (rotation_progress * np.pi)  # Start from top position
        elif cycle == 3:
            empty_slots.update({0, 1, 2, 3})

    draw_launcher(rotation_angle, empty_slots, drop_payload_data)
    ax.text(0, -FUSELAGE_DIAMETER - 0.8, f"Time: {time:.1f}s", fontsize=12, ha='center')

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)

# Initialize plot
init_plot()
draw_fuselage()
draw_gravity_arrow()

# Animate for 20 seconds real time (40 seconds simulation time)
ani = animation.FuncAnimation(fig, update, 
                            frames=20*FPS,  # 20 seconds of real time
                            interval=1000/FPS)  # Interval in milliseconds

# Save the animation
ani.save('outputs/rotary_launcher.gif', writer='pillow', fps=FPS)