import pygame
import random
import math
from typing import Tuple, List
import config

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, width: int, height: int) -> None:
        super().__init__()
        self.width: int = width
        self.height: int = height
        
        self.image: pygame.Surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect: pygame.Rect = pygame.Rect(int(x), int(y), self.width, self.height)
        
        self.x_pos: float = float(x)
        self.animation_time: float = 0.0

    def reset(self, x: float, y: float) -> None:
        """Resets the position of the recycled obstacle."""
        self.x_pos = float(x)
        self.rect.x = int(x)
        self.rect.y = int(y)
        self.animation_time = 0.0

    def update(self, speed: float) -> None:
        """Moves the obstacle from right to left and kills it if off-screen."""
        self.x_pos -= speed
        self.rect.x = int(self.x_pos)
        self.animation_time += 0.2
        
        # Draw procedural asset
        self.draw_obstacle()
        
        # Explicitly kill sprite once it completely leaves the left edge
        if self.rect.right < 0:
            self.kill()

    def draw_obstacle(self) -> None:
        """Must be overridden by subclasses."""
        pass


class Drone(Obstacle):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, config.DRONE_WIDTH, config.DRONE_HEIGHT)

    def draw_obstacle(self) -> None:
        self.image.fill((0, 0, 0, 0))  # Clear surface
        w, h = self.width, self.height
        
        # Hexagonal central hull points
        hull_points = [
            (8, h // 2 - 8),
            (w - 8, h // 2 - 8),
            (w - 2, h // 2),
            (w - 8, h // 2 + 8),
            (8, h // 2 + 8),
            (2, h // 2)
        ]
        
        # Draw Hull
        pygame.draw.polygon(self.image, config.COLOR_BG, hull_points)
        pygame.draw.polygon(self.image, config.COLOR_YELLOW, hull_points, 2)
        
        # Blinking core sensor (Blinks yellow/magenta)
        blink = (math.sin(self.animation_time * 2.0) > 0)
        sensor_color = config.COLOR_YELLOW if blink else config.COLOR_MAGENTA
        pygame.draw.circle(self.image, sensor_color, (w // 2, h // 2), 4)
        pygame.draw.circle(self.image, config.COLOR_WHITE, (w // 2, h // 2), 1.5)
        
        # Thrusters (left/right wings)
        pygame.draw.line(self.image, config.COLOR_CYAN, (2, h // 2), (6, h // 2), 2)
        pygame.draw.line(self.image, config.COLOR_CYAN, (w - 2, h // 2), (w - 6, h // 2), 2)
        
        # Spinning rotors
        rot_angle = self.animation_time * 1.5
        rx1 = math.cos(rot_angle) * 10
        ry1 = math.sin(rot_angle) * 3
        rx2 = -rx1
        ry2 = -ry1
        
        # Left propeller
        pygame.draw.line(self.image, config.COLOR_CYAN, (6, h // 2 - 6), (6 + rx1, h // 2 - 6 + ry1), 1)
        pygame.draw.line(self.image, config.COLOR_CYAN, (6, h // 2 - 6), (6 + rx2, h // 2 - 6 + ry2), 1)
        pygame.draw.circle(self.image, config.COLOR_CYAN, (6, h // 2 - 6), 2)
        
        # Right propeller
        pygame.draw.line(self.image, config.COLOR_CYAN, (w - 6, h // 2 - 6), (w - 6 + rx1, h // 2 - 6 + ry1), 1)
        pygame.draw.line(self.image, config.COLOR_CYAN, (w - 6, h // 2 - 6), (w - 6 + rx2, h // 2 - 6 + ry2), 1)
        pygame.draw.circle(self.image, config.COLOR_CYAN, (w - 6, h // 2 - 6), 2)


class LaserBarrier(Obstacle):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, config.LASER_WIDTH, config.LASER_HEIGHT)

    def draw_obstacle(self) -> None:
        self.image.fill((0, 0, 0, 0))
        w, h = self.width, self.height
        
        # Draw Base support generator (slate box with warning lines)
        base_rect = pygame.Rect(2, h - 14, w - 4, 14)
        pygame.draw.rect(self.image, config.COLOR_BG, base_rect)
        pygame.draw.rect(self.image, config.COLOR_MAGENTA, base_rect, 2, border_radius=2)
        
        # Warning diagonal stripes on base
        pygame.draw.line(self.image, config.COLOR_MAGENTA, (6, h - 2), (w - 6, h - 12), 1)
        
        # Top emitter cap
        cap_rect = pygame.Rect(4, 0, w - 8, 8)
        pygame.draw.rect(self.image, config.COLOR_BG, cap_rect)
        pygame.draw.rect(self.image, config.COLOR_MAGENTA, cap_rect, 2, border_radius=1)
        
        # Drawing Pulsing laser beam
        pulse_width = int(4 + math.sin(self.animation_time * 3.0) * 2)
        laser_rect = pygame.Rect(w // 2 - pulse_width // 2, 8, pulse_width, h - 22)
        
        # Glow surface (blits translucent laser glow)
        glow_surf = pygame.Surface((w, h - 22), pygame.SRCALPHA)
        # Translucent glow
        pygame.draw.rect(glow_surf, (*config.COLOR_MAGENTA, 80), (w // 2 - pulse_width, 0, pulse_width * 2, h - 22), border_radius=3)
        # Bright core
        pygame.draw.rect(glow_surf, (*config.COLOR_WHITE, 230), (w // 2 - pulse_width // 4, 0, max(1, pulse_width // 2), h - 22))
        
        self.image.blit(glow_surf, (0, 8))


class ObstaclePool:
    def __init__(self) -> None:
        self.drones: List[Drone] = []
        self.lasers: List[LaserBarrier] = []

    def get_drone(self) -> Drone:
        """Retrieves an inactive drone or instantiates a new one."""
        for drone in self.drones:
            if not drone.alive():
                drone.reset(config.SCREEN_WIDTH, config.DRONE_FLY_Y)
                return drone
        
        # No free drones; instantiate new and cache
        new_drone = Drone(config.SCREEN_WIDTH, config.DRONE_FLY_Y)
        self.drones.append(new_drone)
        return new_drone

    def get_laser(self) -> LaserBarrier:
        """Retrieves an inactive laser barrier or instantiates a new one."""
        for laser in self.lasers:
            if not laser.alive():
                laser.reset(config.SCREEN_WIDTH, config.LASER_Y)
                return laser
                
        # No free lasers; instantiate new and cache
        new_laser = LaserBarrier(config.SCREEN_WIDTH, config.LASER_Y)
        self.lasers.append(new_laser)
        return new_laser

    def get_active_count(self) -> int:
        """Counts how many obstacles are currently in the active layout."""
        d_active = sum(1 for d in self.drones if d.alive())
        l_active = sum(1 for l in self.lasers if l.alive())
        return d_active + l_active

    def get_total_allocated(self) -> int:
        """Gets total allocated memory structures in the pool."""
        return len(self.drones) + len(self.lasers)
