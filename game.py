import pygame
import random
import os
import math
from typing import Tuple, List, Dict
import config
from player import Player
from obstacle import ObstaclePool, Obstacle, Drone, LaserBarrier
from particle import ParticleEmitter

class Game:
    # State Machine Constants
    STATE_MENU: int = 0
    STATE_PLAYING: int = 1
    STATE_GAME_OVER: int = 2

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(config.SCREEN_TITLE)
        
        # Core Pygame screen and clock
        self.screen: pygame.Surface = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.is_running: bool = True
        self.state: int = self.STATE_MENU

        # Sprites & Performance Groups
        self.player: Player = Player()
        self.obstacle_pool: ObstaclePool = ObstaclePool()
        self.emitter: ParticleEmitter = ParticleEmitter()
        
        # Pygame sprite groups for rendering/collisions
        self.all_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.obstacles_group: pygame.sprite.Group = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        # Game State Variables
        self.score: float = 0.0
        self.high_score: int = self.load_high_score()
        self.game_speed: float = config.OBSTACLE_BASE_SPEED
        
        # Spawning controls
        self.spawn_timer: int = 0  # relative milliseconds
        self.last_spawn_time: int = 0
        
        # Parallax Background System
        self.grid_phase: float = 0.0
        self.stars: List[Dict[str, float]] = []
        self.buildings: List[List[float]] = [] # list of [x_pos, width, height] to allow mutation
        self.init_parallax()
        
        # Fonts (Using Pygame's clean built-in system font fallback)
        self.font_title: pygame.font.Font = pygame.font.Font(None, 74)
        self.font_subtitle: pygame.font.Font = pygame.font.Font(None, 40)
        self.font_hud: pygame.font.Font = pygame.font.Font(None, 24)
        self.font_large: pygame.font.Font = pygame.font.Font(None, 60)

    def init_parallax(self) -> None:
        """Initializes positions for star background and skyline buildings."""
        # 1. Distant Stars
        for _ in range(45):
            self.stars.append({
                "x": random.uniform(0, config.SCREEN_WIDTH),
                "y": random.uniform(10, 320),  # Upper half of screen
                "speed": random.uniform(0.1, 0.4),
                "size": random.uniform(1.0, 3.0)
            })

        # 2. Middle-ground Skyline
        horizon_y = 350
        x = 0.0
        while x < config.SCREEN_WIDTH + 200:
            width = random.randint(60, 130)
            height = random.randint(70, 190)
            self.buildings.append([x, float(width), float(height)])
            x += width + random.randint(15, 50)

    def load_high_score(self) -> int:
        """Loads high score from local text file."""
        if os.path.exists(config.SAVE_FILE):
            try:
                with open(config.SAVE_FILE, "r") as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                return 0
        return 0

    def save_high_score(self) -> None:
        """Saves current score as high score if it exceeds the record."""
        if int(self.score) > self.high_score:
            self.high_score = int(self.score)
            try:
                with open(config.SAVE_FILE, "w") as f:
                    f.write(str(self.high_score))
            except IOError:
                pass  # Suppress save errors to avoid crashes

    def start_game(self) -> None:
        """Resets variables and enters the active running state."""
        self.state = self.STATE_PLAYING
        self.score = 0.0
        self.game_speed = config.OBSTACLE_BASE_SPEED
        self.spawn_timer = 0
        self.last_spawn_time = pygame.time.get_ticks()
        
        # Reset runner position
        self.player.rect.x = config.PLAYER_START_X
        self.player.rect.bottom = config.GROUND_Y
        self.player.vy = 0.0
        self.player.on_ground = True
        self.player.is_ducking = False
        
        # Clear out current obstacles
        for obstacle in self.obstacles_group:
            obstacle.kill()
            
        self.emitter.clear()

    def handle_events(self) -> None:
        """Polls Pygame events and dispatches keys based on state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == self.STATE_PLAYING:
                        self.state = self.STATE_MENU
                    else:
                        self.is_running = False
                        
                elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    if self.state == self.STATE_MENU:
                        self.start_game()
                    elif self.state == self.STATE_PLAYING:
                        self.player.jump(self.emitter)
                    elif self.state == self.STATE_GAME_OVER:
                        self.start_game()
                        
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if self.state == self.STATE_PLAYING:
                        self.player.start_duck()
                        
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    if self.state == self.STATE_PLAYING:
                        self.player.stop_duck()

    def update(self) -> None:
        """Main physics/state updater."""
        current_time = pygame.time.get_ticks()
        
        if self.state == self.STATE_PLAYING:
            # 1. Update difficulty and speed mapping
            self.score += 0.1  # Score increases by distance run
            self.game_speed = min(
                config.OBSTACLE_MAX_SPEED, 
                config.OBSTACLE_BASE_SPEED + (self.score / 100.0) * config.OBSTACLE_SPEED_INCREMENT
            )
            
            # Speed scaling factor
            speed_mult = self.game_speed / config.OBSTACLE_BASE_SPEED
            
            # 2. Obstacle Procedural Spawning
            # Cooldown drops as runner moves faster
            spawn_cooldown = max(
                config.OBSTACLE_MIN_SPAWN_COOLDOWN,
                config.OBSTACLE_MAX_SPAWN_COOLDOWN - int((self.game_speed - config.OBSTACLE_BASE_SPEED) * config.OBSTACLE_SPAWN_DECREASE_RATE)
            )
            
            if current_time - self.last_spawn_time > spawn_cooldown:
                # Add random variance to make patterns less predictable
                variance = random.randint(-150, 150)
                if current_time - self.last_spawn_time > spawn_cooldown + variance:
                    # Choose obstacle type
                    if random.random() > 0.5:
                        obstacle = self.obstacle_pool.get_drone()
                    else:
                        obstacle = self.obstacle_pool.get_laser()
                    
                    self.all_sprites.add(obstacle)
                    self.obstacles_group.add(obstacle)
                    self.last_spawn_time = current_time

            # 3. Update active sprites
            self.player.update(self.emitter, speed_mult)
            self.obstacles_group.update(self.game_speed)
            
            # 4. Collision Detection (Pixel-perfect mask overlap check)
            self.player.mask = pygame.mask.from_surface(self.player.image)
            for obs in self.obstacles_group:
                obs.mask = pygame.mask.from_surface(obs.image)
                if pygame.sprite.collide_mask(self.player, obs):
                    # Spawn impact sparks
                    self.emitter.emit_explosion(self.player.rect.centerx, self.player.rect.centery, config.COLOR_MAGENTA)
                    self.save_high_score()
                    self.state = self.STATE_GAME_OVER
                    break
                    
        # Update scrolling background & particle physics across states
        self.update_background()
        self.emitter.update()

    def update_background(self) -> None:
        """Scrolls stars and skyline parallax lists."""
        scroll_speed = self.game_speed if self.state == self.STATE_PLAYING else 1.5
        
        # Scroll Stars
        for star in self.stars:
            star["x"] -= scroll_speed * star["speed"]
            if star["x"] < -10:
                star["x"] = config.SCREEN_WIDTH + 10
                star["y"] = random.uniform(10, 320)

        # Scroll Skyline
        bg_speed = scroll_speed * 0.12
        for build in self.buildings:
            build[0] -= bg_speed
            
        # Wrap skyline buildings
        for build in self.buildings:
            if build[0] + build[1] < 0:
                # Find furthest right point
                max_x = max(b[0] + b[1] for b in self.buildings)
                build[0] = max_x + random.randint(15, 60)
                build[1] = float(random.randint(60, 130))
                build[2] = float(random.randint(70, 190))

        # Scroll perspective floor grid phase
        self.grid_phase = (self.grid_phase + scroll_speed * 0.4) % 40.0

    def draw_glowing_text(self, text: str, font: pygame.font.Font, color: Tuple[int, int, int], center: Tuple[int, int]) -> None:
        """Renders text with a layered neon glow shadow."""
        # Draw outer glow
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            glow_surf = font.render(text, True, color)
            rect = glow_surf.get_rect(center=(center[0] + dx, center[1] + dy))
            self.screen.blit(glow_surf, rect)
            
        # Draw clean core white text
        core_surf = font.render(text, True, config.COLOR_WHITE)
        rect = core_surf.get_rect(center=center)
        self.screen.blit(core_surf, rect)

    def draw_parallax_and_grid(self) -> None:
        """Draws starry background, parallax neon skyscrapers, and 3D grid."""
        # 1. Fill screen background
        self.screen.fill(config.COLOR_BG)
        horizon_y = 350
        floor_y = config.GROUND_Y
        
        # 2. Draw Stars
        for star in self.stars:
            # Draw blinking stars
            glow = random.randint(100, 255)
            pygame.draw.circle(self.screen, (glow, glow, 255), (int(star["x"]), int(star["y"])), int(star["size"]))

        # 3. Draw Skyline (Skyscrapers with glowing neon windows)
        for build in self.buildings:
            bx, bw, bh = int(build[0]), int(build[1]), int(build[2])
            by = horizon_y - bh
            
            # Draw building body
            pygame.draw.rect(self.screen, (13, 15, 23), (bx, by, bw, bh))
            # Draw dim blue neon outlines
            pygame.draw.rect(self.screen, (32, 38, 54), (bx, by, bw, bh), 1)
            
            # Render rows of windows
            cols = bw // 18
            rows = bh // 24
            for r in range(1, rows):
                for c in range(1, cols):
                    # Deterministic hash to keep window states consistent
                    if (hash((bx, r, c)) % 10) > 7:
                        wx = bx + c * 18
                        wy = by + r * 24
                        pygame.draw.rect(self.screen, config.COLOR_CYAN, (wx, wy, 3, 3))

        # 4. Draw Horizon glow strip
        for i in range(15):
            alpha = int((1.0 - i / 15.0) * 110)
            glow_line = pygame.Surface((config.SCREEN_WIDTH, 2), pygame.SRCALPHA)
            glow_line.fill((*config.COLOR_CYAN, alpha))
            self.screen.blit(glow_line, (0, horizon_y - 10 + i * 2))
            
        pygame.draw.line(self.screen, config.COLOR_CYAN, (0, horizon_y), (config.SCREEN_WIDTH, horizon_y), 2)

        # 5. Draw 3D Perspective Floor Grid
        # Horizontal lines (Quadratic spacing to project depth perspective)
        num_lines = 9
        for i in range(num_lines + 1):
            prog = (i + self.grid_phase / 40.0) / num_lines
            if prog > 1.0:
                continue
            line_y = horizon_y + (prog ** 2.2) * (config.SCREEN_HEIGHT - horizon_y)
            # Lines fade out closer to the horizon
            alpha = int(prog * 180)
            grid_surf = pygame.Surface((config.SCREEN_WIDTH, 1), pygame.SRCALPHA)
            grid_surf.fill((*config.COLOR_GRID, alpha))
            self.screen.blit(grid_surf, (0, int(line_y)))

        # Vertical lines (Converging to a vanishing point at screen center horizon)
        num_v_lines = 22
        vanishing_pt = (config.SCREEN_WIDTH // 2, horizon_y)
        for i in range(num_v_lines):
            # Calculate coordinates along bottom edge of screen
            x_bottom = int((i / (num_v_lines - 1)) * config.SCREEN_WIDTH)
            pygame.draw.line(self.screen, config.COLOR_GRID, vanishing_pt, (x_bottom, config.SCREEN_HEIGHT), 1)

        # 6. Draw Solid neon cyan ground surface line
        pygame.draw.line(self.screen, config.COLOR_CYAN, (0, floor_y), (config.SCREEN_WIDTH, floor_y), 3)

    def draw_hud(self) -> None:
        """Renders in-game parameters: score, high score, multiplier, and pool stats."""
        # Left side info (Score)
        score_txt = f"DIST: {int(self.score)}m"
        score_surf = self.font_subtitle.render(score_txt, True, config.COLOR_WHITE)
        self.screen.blit(score_surf, (20, 20))
        
        # High Score
        high_txt = f"BEST: {self.high_score}m"
        high_surf = self.font_hud.render(high_txt, True, config.COLOR_CYAN)
        self.screen.blit(high_surf, (20, 52))

        # Speed Multiplier HUD widget
        speed_mult = self.game_speed / config.OBSTACLE_BASE_SPEED
        mult_txt = f"SPEED: {speed_mult:.2f}x"
        mult_color = config.COLOR_GREEN if speed_mult < 1.4 else config.COLOR_YELLOW
        mult_surf = self.font_subtitle.render(mult_txt, True, mult_color)
        self.screen.blit(mult_surf, (config.SCREEN_WIDTH - 200, 20))

        # Bottom debug/memory leak monitor (pools status)
        pool_active = self.obstacle_pool.get_active_count()
        pool_total = self.obstacle_pool.get_total_allocated()
        leak_monitor = f"POOL ACTIVE: {pool_active} | POOL TOTAL: {pool_total} | PARTICLES: {len(self.emitter.particles)}"
        monitor_surf = self.font_hud.render(leak_monitor, True, config.COLOR_GRAY)
        self.screen.blit(monitor_surf, (20, config.SCREEN_HEIGHT - 30))

    def draw_menu(self) -> None:
        """Renders main landing screen."""
        self.draw_parallax_and_grid()
        
        # Scanning laser line effect across menu
        scan_y = int(220 + math.sin(pygame.time.get_ticks() * 0.002) * 80)
        scan_surf = pygame.Surface((config.SCREEN_WIDTH, 4), pygame.SRCALPHA)
        scan_surf.fill((*config.COLOR_CYAN, 90))
        self.screen.blit(scan_surf, (0, scan_y))

        # Neon Game Title
        self.draw_glowing_text("CYBER RUNNER", self.font_title, config.COLOR_CYAN, (config.SCREEN_WIDTH // 2, 170))
        
        # High Score record
        record_txt = f"SYSTEM RECORD: {self.high_score} METERS"
        record_surf = self.font_subtitle.render(record_txt, True, config.COLOR_YELLOW)
        record_rect = record_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 230))
        self.screen.blit(record_surf, record_rect)

        # Pulsing prompt text
        pulse_alpha = int(127 + math.sin(pygame.time.get_ticks() * 0.007) * 127)
        pulse_color = (*config.COLOR_GREEN, pulse_alpha)
        
        prompt_surf = self.font_subtitle.render("PRESS SPACE TO INITIALIZE RUN", True, config.COLOR_GREEN)
        # Apply prompt alpha fade
        prompt_temp = pygame.Surface(prompt_surf.get_size(), pygame.SRCALPHA)
        prompt_temp.fill((255, 255, 255, pulse_alpha), special_flags=pygame.BLEND_RGBA_MULT)
        prompt_surf.blit(prompt_temp, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        prompt_rect = prompt_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 310))
        self.screen.blit(prompt_surf, prompt_rect)

        # Tech Controls HUD box
        ctrl_y = 480
        pygame.draw.rect(self.screen, (15, 20, 30), (config.SCREEN_WIDTH // 2 - 250, ctrl_y, 500, 60), border_radius=4)
        pygame.draw.rect(self.screen, config.COLOR_CYAN, (config.SCREEN_WIDTH // 2 - 250, ctrl_y, 500, 60), 1, border_radius=4)
        
        ctrl_txt1 = "UP/W / SPACE : JUMP"
        ctrl_txt2 = "DOWN/S : DUCK & SLIDE"
        c1_surf = self.font_hud.render(ctrl_txt1, True, config.COLOR_WHITE)
        c2_surf = self.font_hud.render(ctrl_txt2, True, config.COLOR_WHITE)
        self.screen.blit(c1_surf, (config.SCREEN_WIDTH // 2 - 220, ctrl_y + 22))
        self.screen.blit(c2_surf, (config.SCREEN_WIDTH // 2 + 30, ctrl_y + 22))

    def draw_game_over(self) -> None:
        """Renders score details and restart instructions."""
        self.draw_parallax_and_grid()
        
        # Draw inactive/crashed player
        self.player.render_character()
        self.screen.blit(self.player.image, self.player.rect)
        
        # Draw active obstacles
        self.obstacles_group.draw(self.screen)
        
        # Draw remaining sparks
        self.emitter.draw(self.screen)

        # Transparent Game Over overlay box
        box_w, box_h = 440, 240
        overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        overlay.fill((10, 11, 16, 210))  # Slate background with opacity
        pygame.draw.rect(overlay, config.COLOR_MAGENTA, (0, 0, box_w, box_h), 2, border_radius=6)
        self.screen.blit(overlay, (config.SCREEN_WIDTH // 2 - box_w // 2, 120))

        # Title
        self.draw_glowing_text("RUN TERMINATED", self.font_large, config.COLOR_MAGENTA, (config.SCREEN_WIDTH // 2, 160))
        
        # Stats
        score_surf = self.font_subtitle.render(f"DISTANCE: {int(self.score)}m", True, config.COLOR_WHITE)
        score_rect = score_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 220))
        self.screen.blit(score_surf, score_rect)

        high_surf = self.font_subtitle.render(f"PERSONAL BEST: {self.high_score}m", True, config.COLOR_YELLOW)
        high_rect = high_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 260))
        self.screen.blit(high_surf, high_rect)

        # Pulsing prompt to restart
        pulse_alpha = int(127 + math.sin(pygame.time.get_ticks() * 0.007) * 127)
        prompt_surf = self.font_hud.render("PRESS SPACE TO REBOOT SYSTEM | ESC TO MENU", True, config.COLOR_GREEN)
        # Apply alpha
        prompt_temp = pygame.Surface(prompt_surf.get_size(), pygame.SRCALPHA)
        prompt_temp.fill((255, 255, 255, pulse_alpha), special_flags=pygame.BLEND_RGBA_MULT)
        prompt_surf.blit(prompt_temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        prompt_rect = prompt_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 315))
        self.screen.blit(prompt_surf, prompt_rect)

    def draw(self) -> None:
        """Central drawing dispatcher."""
        if self.state == self.STATE_MENU:
            self.draw_menu()
        elif self.state == self.STATE_PLAYING:
            self.draw_parallax_and_grid()
            
            # Draw Runner
            self.screen.blit(self.player.image, self.player.rect)
            
            # Draw Obstacles
            self.obstacles_group.draw(self.screen)
            
            # Draw HUD
            self.draw_hud()
            
            # Draw Particles
            self.emitter.draw(self.screen)
            
        elif self.state == self.STATE_GAME_OVER:
            self.draw_game_over()
            
        pygame.display.flip()

    def run(self) -> None:
        """Primary game loop execution capped at config.FPS."""
        while self.is_running:
            self.handle_events()
            self.update()
            self.draw()
            
            # Strictly decouple speed / physics and cap at 60 FPS
            self.clock.tick(config.FPS)
            
        pygame.quit()

