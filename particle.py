import pygame
import random
from typing import Tuple, List
import config

class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: Tuple[int, int, int], radius: float, lifetime: int):
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.color: Tuple[int, int, int] = color
        self.radius: float = radius
        self.max_life: int = lifetime
        self.life: int = lifetime

    def update(self) -> bool:
        """
        Updates particle position and lifetime.
        Returns True if the particle is still alive, False otherwise.
        """
        self.x += self.vx
        self.y += self.vy
        
        # Friction
        self.vx *= 0.96
        self.vy *= 0.96
        
        self.life -= 1
        return self.life > 0

    def draw(self, surface: pygame.Surface) -> None:
        if self.life <= 0 or self.radius <= 0:
            return
            
        # Linear fade alpha
        alpha = int((self.life / self.max_life) * 255)
        alpha = max(0, min(255, alpha))
        
        # Size decay
        current_radius = max(1.0, self.radius * (self.life / self.max_life))
        size = int(current_radius * 3)  # Slightly larger for glow bounding box
        if size < 2:
            size = 2
            
        # Draw glowing particle
        glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw outer neon glow (larger, translucent)
        pygame.draw.circle(glow_surf, (*self.color, alpha // 4), (size // 2, size // 2), size // 2)
        # Draw inner core (smaller, bright white/neon)
        pygame.draw.circle(glow_surf, (255, 255, 255, alpha), (size // 2, size // 2), max(1, int(size // 4)))
        
        surface.blit(glow_surf, (int(self.x - size // 2), int(self.y - size // 2)))


class ParticleEmitter:
    def __init__(self) -> None:
        self.particles: List[Particle] = []

    def emit_trail(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        """Spawns particles trailing behind the player."""
        if len(self.particles) >= config.PARTICLE_MAX_COUNT:
            self.particles.pop(0)  # Evict oldest to maintain cap
            
        # Emit spark drifting backward
        vx = random.uniform(-4.0, -1.0)
        vy = random.uniform(-1.0, 1.0)
        radius = random.uniform(3.0, 6.0)
        lifetime = random.randint(15, 30)
        
        self.particles.append(Particle(x, y, vx, vy, color, radius, lifetime))

    def emit_dust(self, x: float, y: float, color: Tuple[int, int, int], count: int = 8) -> None:
        """Spawns dust particles on jump or landing."""
        for _ in range(count):
            if len(self.particles) >= config.PARTICLE_MAX_COUNT:
                self.particles.pop(0)
            vx = random.uniform(-2.5, 2.5)
            vy = random.uniform(-1.5, -0.2)  # Drift upwards slightly
            radius = random.uniform(4.0, 8.0)
            lifetime = random.randint(20, 40)
            self.particles.append(Particle(x, y, vx, vy, color, radius, lifetime))

    def emit_explosion(self, x: float, y: float, color: Tuple[int, int, int], count: int = 25) -> None:
        """Spawns a dramatic explosion of particles on crash."""
        for _ in range(count):
            if len(self.particles) >= config.PARTICLE_MAX_COUNT:
                self.particles.pop(0)
            # Radial velocity vectors
            angle = random.uniform(0, 6.28)
            speed = random.uniform(2.0, 8.0)
            vx = speed * pygame.math.Vector2(1, 0).rotate_rad(angle).x
            vy = speed * pygame.math.Vector2(1, 0).rotate_rad(angle).y
            
            radius = random.uniform(5.0, 10.0)
            lifetime = random.randint(30, 60)
            
            # Mix the core color with neon orange or yellow sparks
            particle_color = color if random.random() > 0.3 else config.COLOR_ORANGE
            self.particles.append(Particle(x, y, vx, vy, particle_color, radius, lifetime))

    def update(self) -> None:
        """Updates all particles and filters out the dead ones."""
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surface: pygame.Surface) -> None:
        """Renders all active particles."""
        for p in self.particles:
            p.draw(surface)

    def clear(self) -> None:
        """Resets the emitter."""
        self.particles.clear()
