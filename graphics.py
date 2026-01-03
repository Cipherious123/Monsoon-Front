import pygame
import sys
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

MAP_WIDTH = 900
SIDEBAR_WIDTH = WINDOW_WIDTH - MAP_WIDTH

FPS = 60
FONT = pygame.font.SysFont("consolas", 18)

# GUI State
_screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Flood Relief Command")

_clock = pygame.time.Clock()

_current_map = None
_current_sprites = []
_sidebar_data = []

# -----------------------------
# Core Functions
# -----------------------------

def load_map(map_image_path):
    """Load and set the current map background."""
    global _current_map
    _current_map = pygame.image.load(map_image_path).convert()
    _current_map = pygame.transform.scale(_current_map, (MAP_WIDTH, WINDOW_HEIGHT))


def set_sprites(sprite_definitions):
    """
    Replace all current sprites.

    sprite_definitions:
        list of dicts:
        {
            "image": "assets/sprites/boat.png",
            "pos": (x, y)
        }
    """
    global _current_sprites
    _current_sprites = []

    for s in sprite_definitions:
        img = pygame.image.load(s["image"]).convert_alpha()
        rect = img.get_rect(center=s["pos"])
        _current_sprites.append((img, rect))


def clear_sprites():
    """Remove all sprites from the map."""
    global _current_sprites
    _current_sprites = []


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


def _draw_sprites():
    for img, rect in _current_sprites:
        _screen.blit(img, rect)


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
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    _screen.fill((0, 0, 0))

    _draw_map()
    _draw_sprites()
    _draw_sidebar()

    pygame.display.flip()
    _clock.tick(FPS)