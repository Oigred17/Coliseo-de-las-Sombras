# ── HUD: barra de vida, oleada, puntuación ──
import pygame
from settings import *
from spritesheet import load_single_image


class HUD:
    def __init__(self):
        self.hp_bar_frame = None
        self.red_ball = None
        self.blue_bar = None
        self.yellow_bar = None
        self.font = None
        self.font_big = None
        self.font_title = None
        self.message = ""
        self.message_timer = 0

    def init_assets(self):
        """Carga los assets de la barra de vida y fuentes."""
        SCALE = 3
        self.hp_bar_frame = load_single_image("Barra de Vida/Hp bar.png", SCALE)
        self.red_ball = load_single_image("Barra de Vida/red bar.png", SCALE)
        self.blue_bar = load_single_image("Barra de Vida/Blue bar.png", SCALE)
        self.yellow_bar = load_single_image("Barra de Vida/yellow bar.png", SCALE)

        self.font = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_big = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI", 72, bold=True)
        try:
            self.menu_bg = load_single_image("Esecenarios/menu_bg.png")
            self.menu_bg = pygame.transform.scale(self.menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.menu_bg = None

    def show_message(self, text, duration=180):
        self.message = text
        self.message_timer = duration

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.message = ""

    def draw(self, surface, player_hp, max_hp, player_mana, max_mana, player_super, max_super, wave, score, game_state, continue_timer=0):
        bar_x, bar_y = 20, 20

        # Dibujar bola roja de vida por DETRÁS del frame
        if self.red_ball and max_hp > 0:
            ratio = player_hp / max_hp
            h = int(self.red_ball.get_height() * ratio)
            if h > 0:
                sub = self.red_ball.subsurface((0, self.red_ball.get_height() - h, self.red_ball.get_width(), h))
                bx = bar_x + (2 * 3) # offset x * scale
                by = bar_y + (5 * 3) + (self.red_ball.get_height() - h)
                surface.blit(sub, (bx, by))

        # Barra Azul (Mana) - Slot inferior con líneas
        if self.blue_bar and max_mana > 0:
            ratio_mana = player_mana / max_mana
            w = int(self.blue_bar.get_width() * ratio_mana)
            if w > 0:
                sub = self.blue_bar.subsurface((0, 0, w, self.blue_bar.get_height()))
                bb_x = bar_x + (58 * 3)
                bb_y = bar_y + (40 * 3)
                surface.blit(sub, (bb_x, bb_y))

        # Barra Amarilla (Super) - Slot superior liso
        if self.yellow_bar and max_super > 0:
            ratio_super = player_super / max_super
            w = int(self.yellow_bar.get_width() * ratio_super)
            if w > 0:
                sub = self.yellow_bar.subsurface((0, 0, w, self.yellow_bar.get_height()))
                bb_x = bar_x + (62 * 3)
                bb_y = bar_y + (20 * 3)
                surface.blit(sub, (bb_x, bb_y))

        # Dibujar el marco de la barra de vida POR ENCIMA
        if self.hp_bar_frame:
            surface.blit(self.hp_bar_frame, (bar_x, bar_y))

        # Oleada
        wave_text = self.font.render(f"OLEADA {wave + 1}", True, (200, 170, 255))
        surface.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, 12))

        # Puntuación
        score_text = self.font.render(f"Puntos: {score}", True, (255, 220, 100))
        surface.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 20, 12))

        # Texto de HP numérico
        hp_text = self.font.render(f"{player_hp}/{max_hp}", True, WHITE)
        surface.blit(hp_text, (bar_x + 50, bar_y + 80)) # Centrado mejor

        # Mensaje central
        if self.message:
            alpha = 255
            if self.message_timer < 30:
                alpha = int(255 * self.message_timer / 30)
            msg_surf = self.font_big.render(self.message, True, (255, 230, 150))
            msg_surf.set_alpha(alpha)
            mx = SCREEN_WIDTH // 2 - msg_surf.get_width() // 2
            my = SCREEN_HEIGHT // 3
            surface.blit(msg_surf, (mx, my))

        # Pantallas de estado
        if game_state == "menu":
            self._draw_menu(surface)
        elif game_state == "wave_intro":
            pass
        elif game_state == "paused":
            self._draw_pause(surface)
        elif game_state == "gameover":
            self._draw_gameover(surface, continue_timer)
        elif game_state == "victory":
            self._draw_victory(surface)

    def _draw_menu(self, surface):
        if self.menu_bg:
            surface.blit(self.menu_bg, (0, 0))
        else:
            # Fondo oscuro fallback
            for i in range(SCREEN_HEIGHT):
                color = (10 + i // 40, 10 + i // 60, 25 + i // 80)
                pygame.draw.line(surface, color, (0, i), (SCREEN_WIDTH, i))

        # Título arriba (estilo Blasphemous v.4.0.67)
        version_txt = self.font.render("v. 1.0.0 - COLISEO", True, (150, 140, 130))
        surface.blit(version_txt, (SCREEN_WIDTH - version_txt.get_width() - 50, 30))

        # No mostrar opciones de texto para mantener el estilo limpio
        pass

        # Panel de controles flotante
        controls = [
            "A/D [LS] - Mover",
            "ESPACIO [A] - Saltar",
            "J [X] - Atacar",
            "K [B] - Dash",
            "U [Y] - Parry",
            "L [RB] - Magia",
            "H [LB] - Curar"
        ]

        # Dibujar panel a la izquierda
        for i, text in enumerate(controls):
            c_surf = self.font.render(text, True, (180, 180, 190))
            surface.blit(c_surf, (50, 480 + i * 25))

        # Efecto de latido para el texto de inicio
        t = pygame.time.get_ticks()
        import math
        alpha = int(127 + 128 * math.sin(t / 400.0))
        start_txt = self.font_big.render("PRESIONA ENTER PARA COMENZAR", True, WHITE)
        start_txt.set_alpha(alpha)
        surface.blit(start_txt, (SCREEN_WIDTH // 2 - start_txt.get_width() // 2, 600))

    def _draw_pause(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        pause_txt = self.font_title.render("PAUSA", True, (255, 255, 255))
        surface.blit(pause_txt, (SCREEN_WIDTH // 2 - pause_txt.get_width() // 2, 250))
        
        info = self.font.render("Presiona START o ENTER para continuar", True, (200, 200, 200))
        surface.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 350))

    def _draw_gameover(self, surface, continue_timer=0):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((40, 5, 5, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("HAS CAÍDO", True, (255, 80, 80))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))

        if continue_timer > 0:
            secs = int(continue_timer) + 1
            color = (100, 255, 100) if secs > 5 else (255, 100, 100)
            cont_txt = self.font_big.render(f"CONTINUAR?  {secs}s", True, color)
            surface.blit(cont_txt, (SCREEN_WIDTH // 2 - cont_txt.get_width() // 2, 310))

            sub = self.font.render("Presiona ENTER o START para continuar", True, (200, 180, 180))
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 400))
        else:
            sub = self.font_big.render("Presiona ENTER o START para volver al menú", True, (200, 180, 180))
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 350))

    def _draw_victory(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 20, 40, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("¡VICTORIA!", True, (255, 220, 100))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 250))

        sub = self.font_big.render("¡Has conquistado el Coliseo!", True, (180, 200, 255))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 340))

        sub2 = self.font.render("Presiona ENTER o START para jugar de nuevo", True, (160, 160, 180))
        surface.blit(sub2, (SCREEN_WIDTH // 2 - sub2.get_width() // 2, 410))
