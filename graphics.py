import pygame
import sys
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
SPRITE_SIZE = (32,32)
MAP_WIDTH = 900
SIDEBAR_WIDTH = WINDOW_WIDTH - MAP_WIDTH

FPS = 60
FONT = pygame.font.SysFont("consolas", 18)

# GUI State
_screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Flood Relief Command")

_clock = pygame.time.Clock()

_current_map = None
_current_sprites_with_labels = []
_sidebar_data = []

# -----------------------------
# Core Functions
# -----------------------------

def load_map(map_image_path):
    """Load and set the current map background."""
    global _current_map
    _current_map = pygame.image.load(map_image_path).convert()
    _current_map = pygame.transform.scale(_current_map, (MAP_WIDTH, WINDOW_HEIGHT))


def set_sprites_with_labels(sprite_label_list):
    """
    Set sprites with labels underneath.
    
    Args:
        sprite_label_dict: Dictionary mapping (sprite_path, label_text, click_text) to (x, y) coordinates
    """
    global _current_sprites_with_labels
    _current_sprites_with_labels = []
    
    for sprite_label_dict in sprite_label_list:
        for (sprite_path, label, click_text), pos in sprite_label_dict.items():
            # Load and scale sprite to reasonable size (64x64)
            img = pygame.image.load(sprite_path).convert_alpha()
            img = pygame.transform.scale(img, (64, 64))
            rect = img.get_rect(center=pos)
            
            _current_sprites_with_labels.append({
                "image": img,
                "rect": rect,
                "label": label,
                "label_pos": (pos[0], pos[1] + 40), # Position label below sprite
                "click_text":   click_text
            })

def clear_sprites():
    """Remove all sprites from the map."""
    global _current_sprites_with_labels
    _current_sprites_with_labels = []


def set_sidebar_data(lines):
    """
    lines: list of strings
    """
    global _sidebar_data
    _sidebar_data = lines


# -----------------------------
# Rendering Helpers
# -----------------------------

def _draw_map():
    if _current_map:
        _screen.blit(_current_map, (0, 0))


def _draw_sprites_with_labels():
    """Draw sprites with their labels underneath."""
    label_font = pygame.font.SysFont("consolas", 14)
    
    for sprite_data in _current_sprites_with_labels:
        # Draw sprite
        _screen.blit(sprite_data["image"], sprite_data["rect"])
        
        # Draw label
        if sprite_data["label"]:
            label_surface = label_font.render(sprite_data["label"], True, (255, 255, 255))
            label_rect = label_surface.get_rect(center=sprite_data["label_pos"])
            
            # Draw black background for readability
            bg_rect = label_rect.inflate(8, 4)
            pygame.draw.rect(_screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(_screen, (100, 100, 100), bg_rect, 1)
            
            _screen.blit(label_surface, label_rect)


def _draw_sidebar():
    sidebar_rect = pygame.Rect(MAP_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
    pygame.draw.rect(_screen, (30, 30, 30), sidebar_rect)

    y = 20
    for line in _sidebar_data:
        text = FONT.render(line, True, (220, 220, 220))
        _screen.blit(text, (MAP_WIDTH + 20, y))
        y += 25


# -----------------------------
# Main GUI Loop Tick
# -----------------------------

def gui_tick():
    """
    Call this ONCE per turn or inside a loop
    """
    mouse_clicked = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_clicked = True

    if mouse_clicked:
        mouse_pos = pygame.mouse.get_pos()

        for sprite in _current_sprites_with_labels:
            if sprite["rect"].collidepoint(mouse_pos):
                sidebar_text = sprite["click_text"]
                set_sidebar_data(sidebar_text)
    _screen.fill((0, 0, 0))

    _draw_map()
    _draw_sprites_with_labels()
    _draw_sidebar()

    pygame.display.flip()
    _clock.tick(FPS)