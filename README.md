# Fire Response Optimization System

A Python-based optimization system for aerial firefighting response times within a defined area of interest.

## Project Overview

This system optimizes the placement of aircraft launch sites to ensure complete coverage of a 28.7 nautical mile square area, with the requirement to reach any potential fire location within 10 minutes.

### Key Parameters
- Area of Interest: 28.7 nautical miles × 28.7 nautical miles
- Grid Resolution: 20m × 20m
- Response Time Limit: 10 minutes
- Launch Time: 30 seconds
- Cruise Speed Range: 40-100 knots
- Number of Initial Sites: 9

### Features
1. Grid-based simulation system
2. Multi-variable optimization for launch site placement
3. Time-to-target calculations considering:
   - Launch/takeoff time (30 seconds)
   - Cruise speed
   - Aircraft turning constraints
   
### Visualizations
1. Heatmap showing optimal base locations based on speed
2. Animated simulation showing:
   - Launch site locations
   - Aircraft path to target
   - Real-time response visualization
   - Aircraft banking/turning mechanics

## Project Structure

project/
├── src/
│   ├── bases/          # Base optimization code
│   ├── fire/           # Fire simulation code
│   └── payload/        # Payload deployment code
├── outputs/
│   ├── base_optimization/  # Base placement optimization results
│   ├── base_coverage/      # Coverage analysis outputs
│   ├── fire_simulations/   # Individual fire simulation results
│   └── fire_grids/         # Combined fire simulation grids
└── README.md