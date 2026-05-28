import pygame
import math
from typing import Tuple
import config
from particle import ParticleEmitter

class Player(pygame.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        # Dimensions
        self.width: int = config.PLAYER_WIDTH
        self.height: int = config.PLAYER_HEIGHT
        
        # Create standard Pygame Sprite properties
        self.image: pygame.Surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect: pygame.Rect = pygame.Rect(config.PLAYER_START_X, config.GROUND_Y - self.height, self.width, self.height)
        
        # Kinematics
        self.vy: float = 0.0
        self.on_ground: bool = True
        
        # States
        self.is_ducking: bool = False
        
        # Procedural Animation Counters
        self.animation_time: float = 0.0
        
    def jump(self, emitter: ParticleEmitter) -> bool:
        """Triggers a jump if the runner is on the ground and not ducking."""
        if self.on_ground and not self.is_ducking:
            self.vy = config.JUMP_FORCE
            self.on_ground = False
            # Emit dust explosion at feet
            emitter.emit_dust(self.rect.centerx, config.GROUND_Y, config.COLOR_CYAN, count=12)
            return True
        return False

    def start_duck(self) -> bool:
        """Transitions into ducking state, shrinking the collision hitbox."""
        if self.on_ground and not self.is_ducking:
            self.is_ducking = True
            self.height = config.PLAYER_DUCK_HEIGHT
            # Re-position rect to remain anchored to ground
            old_bottom = self.rect.bottom
            self.rect.height = self.height
            self.rect.bottom = old_bottom
            return True
        return False

    def stop_duck(self) -> None:
        """Transitions out of ducking state, restoring original hitbox size."""
        if self.is_ducking:
            self.is_ducking = False
            self.height = config.PLAYER_HEIGHT
            # Re-position rect upward
            old_bottom = self.rect.bottom
            self.rect.height = self.height
            self.rect.bottom = old_bottom

    def update_physics(self, emitter: ParticleEmitter) -> None:
        """Applies gravity and updates the player's vertical position."""
        if not self.on_ground:
            self.vy += config.GRAVITY
            self.rect.y += int(self.vy)
            
            # Floor boundary check
            if self.rect.bottom >= config.GROUND_Y:
                self.rect.bottom = config.GROUND_Y
                self.vy = 0.0
                if not self.on_ground:
                    self.on_ground = True
                    # Emit landing landing puff
                    emitter.emit_dust(self.rect.centerx, config.GROUND_Y, config.COLOR_GREEN, count=10)
        
    def update(self, emitter: ParticleEmitter, speed_multiplier: float = 1.0) -> None:
        """Updates physics and redraws the procedural runner sprite."""
        self.update_physics(emitter)
        
        # Increment animation tick relative to scrolling speed
        self.animation_time += 0.25 * speed_multiplier
        
        # Emit neon trails behind the player while running
        if self.on_ground and not self.is_ducking:
            if math.sin(self.animation_time) > 0.0:  # Emit trails periodically
                # Visor trail
                emitter.emit_trail(self.rect.left + 5, self.rect.top + 10, config.COLOR_CYAN)
                # Feet sparks
                emitter.emit_trail(self.rect.left + 8, self.rect.bottom - 4, config.COLOR_GREEN)
        
        # Re-render procedural character image
        self.render_character()

    def render_character(self) -> None:
        """Procedurally draws the cyberrunner with neon details."""
        # Refresh drawing surface
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # Clear surface
        
        w, h = self.width, self.height
        
        if self.is_ducking:
            # --- DUCKING RENDER (Sleek slider posture) ---
            # Body/Torso (magenta/cyan cybernetic slide)
            body_rect = pygame.Rect(4, h - 20, w - 8, 16)
            pygame.draw.rect(self.image, config.COLOR_BG, body_rect)
            pygame.draw.rect(self.image, config.COLOR_CYAN, body_rect, 2, border_radius=4)
            
            # Cyber visor (glowing forward strip)
            visor_rect = pygame.Rect(w - 14, h - 26, 12, 6)
            pygame.draw.rect(self.image, config.COLOR_CYAN, visor_rect, border_radius=2)
            pygame.draw.rect(self.image, config.COLOR_WHITE, (w - 10, h - 25, 6, 2))
            
            # Sliding sparks/thruster under the slider
            slide_line = ((8, h - 2), (w - 8, h - 2))
            pygame.draw.line(self.image, config.COLOR_GREEN, slide_line[0], slide_line[1], 2)
            
        else:
            # --- UPRIGHT RUNNING/JUMPING RENDER ---
            # Legs motion
            if self.on_ground:
                # Running cycle legs (using math.sin)
                swing_1 = math.sin(self.animation_time) * 12
                swing_2 = -math.sin(self.animation_time) * 12
                
                # Front leg
                foot1_x = w // 2 + swing_1
                pygame.draw.line(self.image, config.COLOR_GREEN, (w // 2, h - 28), (foot1_x, h - 2), 3)
                pygame.draw.circle(self.image, config.COLOR_WHITE, (int(foot1_x), h - 2), 3)
                
                # Back leg
                foot2_x = w // 2 + swing_2
                pygame.draw.line(self.image, config.COLOR_CYAN, (w // 2 - 2, h - 28), (foot2_x, h - 2), 3)
                pygame.draw.circle(self.image, config.COLOR_CYAN, (int(foot2_x), h - 2), 3)
            else:
                # Jumping tuck posture
                # Front leg curled
                pygame.draw.line(self.image, config.COLOR_GREEN, (w // 2, h - 28), (w // 2 + 10, h - 14), 3)
                pygame.draw.line(self.image, config.COLOR_GREEN, (w // 2 + 10, h - 14), (w // 2 - 2, h - 8), 3)
                # Back leg extended down slightly
                pygame.draw.line(self.image, config.COLOR_CYAN, (w // 2 - 4, h - 28), (w // 2 - 8, h - 10), 3)

            # Torso (Sleek angular cyber armor)
            torso_points = [(8, h - 30), (w - 8, h - 34), (w - 10, h - 16), (10, h - 16)]
            pygame.draw.polygon(self.image, config.COLOR_BG, torso_points)
            pygame.draw.polygon(self.image, config.COLOR_CYAN, torso_points, 2)
            
            # Glowing Core (Center of Torso)
            core_y = h - 24
            pygame.draw.circle(self.image, config.COLOR_GREEN, (w // 2, core_y), 4)
            pygame.draw.circle(self.image, config.COLOR_WHITE, (w // 2, core_y), 1.5)
            
            # Head (Drifting above torso)
            head_center = (w // 2 - 2, 14)
            pygame.draw.circle(self.image, config.COLOR_BG, head_center, 8)
            pygame.draw.circle(self.image, config.COLOR_CYAN, head_center, 8, 2)
            
            # Glowing Visor
            visor_points = [(w // 2 + 1, 10), (w // 2 + 6, 12), (w // 2 + 4, 16), (w // 2 - 1, 15)]
            pygame.draw.polygon(self.image, config.COLOR_CYAN, visor_points)
            pygame.draw.polygon(self.image, config.COLOR_WHITE, [(w // 2 + 2, 11), (w // 2 + 5, 12), (w // 2 + 4, 14), (w // 2 + 1, 13)])
            
            # Tech shoulder joint details
            pygame.draw.circle(self.image, config.COLOR_CYAN, (8, h - 28), 2.5)
