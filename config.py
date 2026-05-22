from typing import Tuple

# Screen Settings
SCREEN_WIDTH: int = 1024
SCREEN_HEIGHT: int = 576
SCREEN_TITLE: str = "Cyber Runner"
FPS: int = 60

# Neon Color Palette (RGB)
COLOR_BG: Tuple[int, int, int] = (10, 11, 16)         # Deep slate/black
COLOR_GRID: Tuple[int, int, int] = (25, 30, 45)       # Dim grid blue
COLOR_CYAN: Tuple[int, int, int] = (0, 255, 255)      # Neon Cyan (Visor, trails, items)
COLOR_MAGENTA: Tuple[int, int, int] = (255, 0, 255)   # Neon Magenta (Laser barriers, warnings)
COLOR_GREEN: Tuple[int, int, int] = (57, 255, 20)     # Neon Green (Player details, speed indicator)
COLOR_YELLOW: Tuple[int, int, int] = (255, 240, 0)    # Neon Yellow (Drones, warnings)
COLOR_ORANGE: Tuple[int, int, int] = (255, 95, 31)    # Neon Orange (Particles, energy)
COLOR_WHITE: Tuple[int, int, int] = (255, 255, 255)   # HUD text highlights
COLOR_GRAY: Tuple[int, int, int] = (100, 100, 110)    # Disabled/secondary text

# Physics Settings
GROUND_Y: int = 460
GRAVITY: float = 0.85
JUMP_FORCE: float = -17.0

# Player Dimensions and Settings
PLAYER_START_X: int = 120
PLAYER_WIDTH: int = 36
PLAYER_HEIGHT: int = 64
PLAYER_DUCK_HEIGHT: int = 32

# Obstacle Settings
OBSTACLE_BASE_SPEED: float = 7.0
OBSTACLE_MAX_SPEED: float = 16.0
OBSTACLE_SPEED_INCREMENT: float = 0.15      # Speed added per 100 score/meters
OBSTACLE_MIN_SPAWN_COOLDOWN: int = 900       # Minimum ms between spawns
OBSTACLE_MAX_SPAWN_COOLDOWN: int = 2200      # Maximum ms between spawns
OBSTACLE_SPAWN_DECREASE_RATE: float = 50.0   # How fast spawn cooldown decreases per speed increment

# Drone Properties
DRONE_WIDTH: int = 40
DRONE_HEIGHT: int = 28
DRONE_FLY_Y: int = GROUND_Y - PLAYER_DUCK_HEIGHT - 12  # Low enough to require ducking, high enough to pass over if ducking

# Laser Barrier Properties
LASER_WIDTH: int = 24
LASER_HEIGHT: int = 50
LASER_Y: int = GROUND_Y - LASER_HEIGHT

# Particles & Aesthetics
PARTICLE_MAX_COUNT: int = 200
TRAIL_EMIT_RATE: float = 0.15 # Chance to spawn trail particle per frame
SAVE_FILE: str = "highscore.txt"
