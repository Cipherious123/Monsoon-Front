import pygame
import sys

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 650
MAP_WIDTH = 1040
SIDEBAR_WIDTH = WINDOW_WIDTH - MAP_WIDTH
FPS = 60

# GUI State (pure data)
_current_map = None
_current_sprites_with_labels = []
_sidebar_data = []
_original_sidebar_data = []  # Store original sidebar text
_clicked_sprite_index = None  # Track which sprite is clicked (None if none)

# Runtime-only pygame objects
_screen = None
FONT = None

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
        list of sprite_label_dict
        sprite_label_dict: Dictionary mapping (sprite_path, label_text, click_text) to (x, y) coordinates
    """
    global _current_sprites_with_labels, _clicked_sprite_index
    _current_sprites_with_labels = []
    _clicked_sprite_index = None  # Reset clicked state when sprites change
    
    for sprite_label_dict in sprite_label_list:
        for (sprite_path, label, click_text), pos in sprite_label_dict.items():
            # Load sprite with alpha channel preserved
            img = pygame.image.load(sprite_path).convert_alpha()
            img = pygame.transform.scale(img, (32, 32))
            rect = img.get_rect(center=pos)
            
            _current_sprites_with_labels.append({
                "image": img,
                "rect": rect,
                "label": label,
                "label_pos": (pos[0], pos[1] + 40), # Position label below sprite
                "click_text": click_text,
            })

def clear_sprites():
    """Remove all sprites from the map."""
    global _current_sprites_with_labels, _clicked_sprite_index
    _current_sprites_with_labels = []
    _clicked_sprite_index = None


def set_sidebar_data(lines):
    """
    lines: list of strings
    """
    global _sidebar_data, _original_sidebar_data, _clicked_sprite_index
    _sidebar_data = lines
    _original_sidebar_data = lines  # Store original for restoration
    # If a sprite is clicked, keep showing its text instead of updating
    if _clicked_sprite_index is None:
        pass  # sidebar_data is already set
    # Otherwise, keep showing the clicked sprite's text


# -----------------------------
# Rendering Helpers
# -----------------------------

def _draw_map():
    if _current_map:
        _screen.blit(_current_map, (0, 0))


def _draw_sprites_with_labels():
    """Draw sprites with their labels underneath (multiline compatible)."""
    
    label_font = pygame.font.SysFont("consolas", 10)
    line_spacing = 2  # spacing between lines
    
    for i, sprite_data in enumerate(_current_sprites_with_labels):
        # --- Draw sprite with proper alpha blending ---
        image = sprite_data["image"]
        
        # Highlight sprite if it's clicked
        if i == _clicked_sprite_index:
            # Draw a circle or border around clicked sprite
            pygame.draw.circle(_screen, (255, 255, 0), sprite_data["rect"].center, 20, 2)
        
        _screen.blit(image, sprite_data["rect"])
        
        # --- Draw multiline label ---
        label = sprite_data["label"]
        if not label:
            continue
        
        lines = label.split("\n")
        rendered_lines = [
            label_font.render(line, True, (255, 255, 255))
            for line in lines
        ]
        
        # Calculate total label block size
        width = max(surf.get_width() for surf in rendered_lines)
        height = sum(surf.get_height() for surf in rendered_lines) + \
                 line_spacing * (len(rendered_lines) - 1)
        
        # Center the whole block at label_pos
        block_rect = pygame.Rect(0, 0, width, height)
        block_rect.center = sprite_data["label_pos"]
        
        # Background for entire label block
        bg_rect = block_rect.inflate(6, 4)
        pygame.draw.rect(_screen, (0, 0, 0), bg_rect)
        pygame.draw.rect(_screen, (80, 80, 80), bg_rect, 1)
        
        # Blit each line
        y = block_rect.top
        for surf in rendered_lines:
            line_rect = surf.get_rect(
                centerx=block_rect.centerx,
                top=y
            )
            _screen.blit(surf, line_rect)
            y += surf.get_height() + line_spacing

def _draw_sidebar():
    sidebar_rect = pygame.Rect(MAP_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
    pygame.draw.rect(_screen, (30, 30, 30), sidebar_rect)

    y = 20

    # Use current sidebar data (which may be overwritten by click)
    if isinstance(_sidebar_data, str):
        lines = _sidebar_data.splitlines()
    else:
        lines = _sidebar_data

    for line in lines:
        text = FONT.render(line, True, (220, 220, 220))
        _screen.blit(text, (MAP_WIDTH + 20, y))
        y += 25


def _handle_sprite_click(pos):
    """Handle mouse click on sprites."""
    global _sidebar_data, _clicked_sprite_index
    
    for i, sprite_data in enumerate(_current_sprites_with_labels):
        if sprite_data["rect"].collidepoint(pos):
            # Toggle: if same sprite clicked, restore original
            if _clicked_sprite_index == i:
                _sidebar_data = _original_sidebar_data
                _clicked_sprite_index = None
            else:
                # New sprite clicked, show its click_text
                _sidebar_data = sprite_data["click_text"]
                _clicked_sprite_index = i
            return
    
    # Click outside any sprite - restore original
    if _clicked_sprite_index is not None:
        _sidebar_data = _original_sidebar_data
        _clicked_sprite_index = None


# -----------------------------
# Main GUI Loop Tick
# -----------------------------

def gui_loop():
    global _screen, FONT

    pygame.init()
    # Use SRCALPHA flag to enable proper alpha blending
    _screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    pygame.display.set_caption("Flood Relief Command")
    FONT = pygame.font.SysFont("consolas", 10)

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    _handle_sprite_click(event.pos)

        _screen.fill((0, 0, 0))
        _draw_map()
        _draw_sprites_with_labels()
        _draw_sidebar()

        pygame.display.flip()
        clock.tick(30)