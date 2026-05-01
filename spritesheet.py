# ── Carga y recorte de spritesheets ──
import os
import pygame
from settings import SPRITES_DIR


def load_spritesheet(path, frame_width, frame_height, num_frames, scale=1, flip=False):
    """Carga un spritesheet y devuelve lista de frames (soporta múltiples filas)."""
    full = os.path.join(SPRITES_DIR, path)
    try:
        sheet = pygame.image.load(full).convert_alpha()
    except pygame.error as e:
        print(f"[WARN] No se pudo cargar sprite: {path} -> {e}")
        surf = pygame.Surface((int(frame_width * scale), int(frame_height * scale)), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 180))
        return [surf]

    cols = sheet.get_width() // frame_width
    rows = sheet.get_height() // frame_height
    total_avail = cols * rows
    
    if num_frames <= 0:
        num_frames = total_avail

    frames = []
    for i in range(num_frames):
        if i >= total_avail: break
        col = i % cols
        row = i // cols
        rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
        frame = sheet.subsurface(rect).copy()
        
        if scale != 1:
            frame = pygame.transform.scale(frame, (int(frame_width * scale), int(frame_height * scale)))
        if flip:
            frame = pygame.transform.flip(frame, True, False)
        frames.append(frame)

    if not frames:
        surf = pygame.Surface((int(frame_width * scale), int(frame_height * scale)), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 180))
        return [surf]

    return frames


def load_single_image(path, scale=1):
    """Carga una imagen individual."""
    full = os.path.join(SPRITES_DIR, path)
    try:
        img = pygame.image.load(full).convert_alpha()
    except pygame.error as e:
        print(f"[WARN] No se pudo cargar imagen: {path} -> {e}")
        img = pygame.Surface((16, 16), pygame.SRCALPHA)
        img.fill((255, 0, 255, 180))
    if scale != 1:
        img = pygame.transform.scale(
            img, (int(img.get_width() * scale), int(img.get_height() * scale))
        )
    return img


def load_tiled_image(path, scale=1):
    """Carga una imagen que se repite (tileable) para fondos."""
    full = os.path.join(SPRITES_DIR, path)
    try:
        img = pygame.image.load(full).convert_alpha()
    except pygame.error:
        img = pygame.Surface((256, 256), pygame.SRCALPHA)
        img.fill((40, 30, 50, 255))
    if scale != 1:
        img = pygame.transform.scale(
            img, (int(img.get_width() * scale), int(img.get_height() * scale))
        )
    return img
