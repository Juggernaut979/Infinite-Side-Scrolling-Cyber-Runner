import math
import struct
import pygame
from typing import Optional

class SoundManager:
    def __init__(self) -> None:
        self.enabled: bool = False
        try:
            # Initialize mixer if not already done. 
            # We configure it for 22050Hz, 16-bit signed, mono output.
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self.enabled = True
        except Exception as e:
            print(f"Warning: Could not initialize pygame.mixer: {e}")
            return
            
        # Synthesize and pre-cache our retro sound effects
        self.snd_jump: Optional[pygame.mixer.Sound] = self._synthesize_sweep(180.0, 520.0, 0.15, 0.22, "sine")
        self.snd_slide: Optional[pygame.mixer.Sound] = self._synthesize_sweep(380.0, 160.0, 0.22, 0.20, "triangle")
        self.snd_crash: Optional[pygame.mixer.Sound] = self._synthesize_crash(180.0, 40.0, 0.55, 0.40)
        self.snd_start: Optional[pygame.mixer.Sound] = self._synthesize_start_chord()
        self.snd_score: Optional[pygame.mixer.Sound] = self._synthesize_sweep(523.25, 1046.50, 0.12, 0.15, "sine")  # C5 to C6 sweep

    def _synthesize_sweep(self, f_start: float, f_end: float, duration: float, volume: float, wave_type: str) -> Optional[pygame.mixer.Sound]:
        """Synthesizes a frequency sweep (pitch slide) with an amplitude decay envelope."""
        if not self.enabled:
            return None
        try:
            sample_rate = 22050
            num_samples = int(sample_rate * duration)
            buffer = bytearray()
            
            for i in range(num_samples):
                t = i / sample_rate
                progress = i / num_samples
                
                # Linearly interpolate frequency
                freq = f_start + (f_end - f_start) * progress
                angle = 2.0 * math.pi * freq * t
                
                # Generate waveform value between -1.0 and 1.0
                if wave_type == "sine":
                    val = math.sin(angle)
                elif wave_type == "square":
                    val = 1.0 if math.sin(angle) >= 0 else -1.0
                elif wave_type == "triangle":
                    # Triangle wave formula
                    val = 2.0 * abs(2.0 * (angle / (2.0 * math.pi) - math.floor(angle / (2.0 * math.pi) + 0.5))) - 1.0
                else:
                    val = math.sin(angle)
                    
                # Apply decay envelope (fade out)
                envelope = 1.0 - progress
                val *= envelope * volume
                val = max(-1.0, min(1.0, val))
                
                # Convert float sample to 16-bit signed integer
                sample = int(val * 32767)
                buffer.extend(struct.pack('<h', sample))
                
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception as e:
            print(f"Error synthesizing sound sweep: {e}")
            return None

    def _synthesize_crash(self, f_start: float, f_end: float, duration: float, volume: float) -> Optional[pygame.mixer.Sound]:
        """Synthesizes a distorted explosion/crash sound using mixed noise and square waves."""
        if not self.enabled:
            return None
        try:
            sample_rate = 22050
            num_samples = int(sample_rate * duration)
            buffer = bytearray()
            import random
            
            for i in range(num_samples):
                t = i / sample_rate
                progress = i / num_samples
                
                # Low frequency downward sweep
                freq = f_start + (f_end - f_start) * progress
                angle = 2.0 * math.pi * freq * t
                
                # Mix: 50% square wave (distorted pitch), 50% white noise
                wave_val = 1.0 if math.sin(angle) >= 0 else -1.0
                noise_val = random.uniform(-1.0, 1.0)
                val = 0.5 * wave_val + 0.5 * noise_val
                
                # Sharp attack, exponential decay envelope
                envelope = (1.0 - progress) ** 2.0
                val *= envelope * volume
                val = max(-1.0, min(1.0, val))
                
                sample = int(val * 32767)
                buffer.extend(struct.pack('<h', sample))
                
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception as e:
            print(f"Error synthesizing crash: {e}")
            return None

    def _synthesize_start_chord(self) -> Optional[pygame.mixer.Sound]:
        """Synthesizes an 8-bit retro ascending arpeggio chord (C4 -> E4 -> G4 -> C5)."""
        if not self.enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.35
            num_samples = int(sample_rate * duration)
            buffer = bytearray()
            
            # Arpeggio note frequencies in Hz
            notes = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
            
            for i in range(num_samples):
                t = i / sample_rate
                progress = i / num_samples
                
                # Cycle through the notes based on progress
                note_idx = min(int(progress * len(notes)), len(notes) - 1)
                freq = notes[note_idx]
                
                angle = 2.0 * math.pi * freq * t
                
                # Square wave for that classic chiptune crunch
                val = 1.0 if math.sin(angle) >= 0 else -1.0
                
                # Linear decay envelope
                envelope = 1.0 - progress
                val *= envelope * 0.18  # Moderate volume
                val = max(-1.0, min(1.0, val))
                
                sample = int(val * 32767)
                buffer.extend(struct.pack('<h', sample))
                
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception as e:
            print(f"Error synthesizing start chord: {e}")
            return None

    def play_jump(self) -> None:
        if self.enabled and self.snd_jump:
            self.snd_jump.play()

    def play_slide(self) -> None:
        if self.enabled and self.snd_slide:
            self.snd_slide.play()

    def play_crash(self) -> None:
        if self.enabled and self.snd_crash:
            self.snd_crash.play()

    def play_start(self) -> None:
        if self.enabled and self.snd_start:
            self.snd_start.play()

    def play_score(self) -> None:
        if self.enabled and self.snd_score:
            self.snd_score.play()
