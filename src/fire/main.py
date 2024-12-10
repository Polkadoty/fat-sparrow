import argparse
from fire_system import FireSystem, WindConditions
from visualization import FireVisualizer
import matplotlib.pyplot as plt
import imageio
import os
import numpy as np
from PIL import Image

def create_image_grid(image_files, output_path, grid_size=None):
    """Create a grid of images from the given files"""
    images = [Image.open(f) for f in image_files]
    n = len(images)
    
    if grid_size is None:
        # Calculate grid dimensions
        cols = int(np.ceil(np.sqrt(n)))
        rows = int(np.ceil(n / cols))
    else:
        rows, cols = grid_size
    
    # Create blank image
    w, h = images[0].size
    grid = Image.new('RGB', (w * cols, h * rows))
    
    # Paste images into grid
    for idx, img in enumerate(images):
        i = idx // cols
        j = idx % cols
        grid.paste(img, (j * w, i * h))
    
    grid.save(output_path)

def create_gif_grid(gif_files, output_path, grid_size=None):
    """Create a grid of GIFs from the given files"""
    print(f"Creating animation grid from {len(gif_files)} files...")
    
    try:
        gifs = [imageio.get_reader(f) for f in gif_files]
        n = len(gifs)
        
        if grid_size is None:
            # Calculate grid dimensions
            cols = int(np.ceil(np.sqrt(n)))
            rows = int(np.ceil(n / cols))
        else:
            rows, cols = grid_size
        
        # Get first frame to determine dimensions
        first_frames = [gif.get_next_data() for gif in gifs]
        h, w = first_frames[0].shape[:2]
        
        # Create writer for output gif
        writer = imageio.get_writer(output_path, fps=30)
        
        # Reset gif readers
        gifs = [imageio.get_reader(f) for f in gif_files]
        
        # Get total number of frames from first gif
        num_frames = len(gifs[0])
        print(f"Processing {num_frames} frames...")
        
        # Process each frame
        for frame_idx in range(num_frames):
            if frame_idx % 10 == 0:  # Progress update every 10 frames
                print(f"Processing frame {frame_idx}/{num_frames}")
                
            frames = []
            for gif in gifs:
                try:
                    if frame_idx < len(gif):
                        frame = gif.get_next_data()
                        # Convert RGBA to RGB if necessary
                        if frame.shape[-1] == 4:
                            frame = frame[..., :3]
                        frames.append(frame)
                    else:
                        frames.append(np.zeros((h, w, 3), dtype=np.uint8))
                except Exception as e:
                    print(f"Error reading frame: {e}")
                    frames.append(np.zeros((h, w, 3), dtype=np.uint8))
            
            # Create grid frame
            grid_frame = np.zeros((h * rows, w * cols, 3), dtype=np.uint8)
            for idx, frame in enumerate(frames):
                i = idx // cols
                j = idx % cols
                grid_frame[i*h:(i+1)*h, j*w:(j+1)*w] = frame
            
            writer.append_data(grid_frame)
        
        print("Finalizing animation grid...")
        writer.close()
        for gif in gifs:
            gif.close()
        print(f"Animation grid saved to {output_path}")
        
    except Exception as e:
        print(f"Error creating animation grid: {e}")
        raise

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num_runs', type=int, default=1,
                       help='Number of simulation runs')
    args = parser.parse_args()
    
    # Create outputs directory
    os.makedirs('outputs', exist_ok=True)
    
    gif_files = []
    final_state_files = []
    
    for i in range(args.num_runs):
        print(f"Running simulation {i+1}/{args.num_runs}")
        
        # Initialize fire system
        fire_system = FireSystem(grid_size=150)
        fire_system.start_fire((75, 75), radius=10)
        
        # Create visualizer and run animation
        visualizer = FireVisualizer(fire_system)
        
        # Set unique filenames for this run
        gif_name = f'outputs/fire_spread_{i}.gif'
        final_state_name = f'outputs/fire_final_state_{i}.png'
        
        gif_files.append(gif_name)
        final_state_files.append(final_state_name)
        
        visualizer.animate_fire(gif_name=gif_name, final_state_name=final_state_name)
        print(f"Completed simulation {i+1}")
    
    if args.num_runs > 1:
        print("\nCreating final grid layouts...")
        # Create grid layouts
        create_image_grid(final_state_files, 'outputs/final_states_grid.png')
        print("Created final states grid")
        
        create_gif_grid(gif_files, 'outputs/animations_grid.gif')
        print("Created animations grid")
        
        print("\nAll outputs saved in outputs/ directory:")
        print("- Individual simulation GIFs: fire_spread_[0-N].gif")
        print("- Individual final states: fire_final_state_[0-N].png")
        print("- Combined grids: final_states_grid.png and animations_grid.gif")

if __name__ == "__main__":
    main()
