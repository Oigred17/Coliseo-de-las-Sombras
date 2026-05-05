# ── HUD: barra de vida, oleada, puntuación ──
import pygame
import math
from settings import *
from spritesheet import load_single_image


class HUD:
    def __init__(self):
        self.hp_bar_frame = None
        self.red_ball = None
        self.blue_bar = None
        self.yellow_bar = None
        self.banner = None
        self.font = None
        self.font_big = None
        self.font_title = None
        self.message = ""
        self.message_timer = 0
        self.message_color = (255, 230, 150)  # Color por defecto del mensaje

        # ── Menu state ──
        self.menu_selection = 0       # 0=Jugar, 1=Entrenamiento, 2=Seleccionar Oleada, 3=Controles
        self.menu_options = ["JUGAR", "ENTRENAMIENTO", "SELECCIONAR OLEADA", "CONTROLES"]
        self.sub_menu = None          # None, "wave_select", "controls"
        self.wave_selection = 0       # Índice de oleada seleccionada
        self.wave_labels = []         # Se llena al init
        self.controls_scroll = 0
        self.menu_anim_t = 0

        # Construir etiquetas de oleadas
        self._build_wave_labels()

    def _build_wave_labels(self):
        """Genera las etiquetas de cada oleada basándose en WAVES de settings."""
        self.wave_labels = []
        for i, wave in enumerate(WAVES):
            if "boss" in wave:
                boss_names = {
                    "frost_guardian": "FROST GUARDIAN",
                    "golem": "STONE GOLEM",
                    "demon_slime": "DEMON SLIME",
                }
                name = boss_names.get(wave["boss"], wave["boss"].upper())
                self.wave_labels.append(f"OLEADA {i+1} - JEFE: {name}")
            else:
                total = sum(v for k, v in wave.items() if isinstance(v, int))
                self.wave_labels.append(f"OLEADA {i+1} - {total} ENEMIGOS")

    def init_assets(self):
        """Carga los assets de la barra de vida y fuentes."""
        self.scale = 2 # Reducido de 3 a 2
        S = self.scale
        self.hp_bar_frame = load_single_image("Barra de Vida/Hp bar.png", S)
        self.red_ball = load_single_image("Barra de Vida/red bar.png", S)
        self.blue_bar = load_single_image("Barra de Vida/Blue bar.png", S)
        self.yellow_bar = load_single_image("Barra de Vida/yellow bar.png", S)

        self.font = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_big = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI", 72, bold=True)
        self.font_menu = pygame.font.SysFont("Segoe UI", 36, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 18)
        try:
            self.menu_bg = load_single_image("Esecenarios/menu_bg.png")
            self.menu_bg = pygame.transform.scale(self.menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.menu_bg = None

        try:
            self.banner = pygame.image.load(resource_path("banner-universidad-de-la-sierra-sur.png")).convert_alpha()
            # Escalar si es muy grande (opcional, pero buena práctica)
            max_w = 300
            if self.banner.get_width() > max_w:
                ratio = max_w / self.banner.get_width()
                new_size = (int(self.banner.get_width() * ratio), int(self.banner.get_height() * ratio))
                self.banner = pygame.transform.scale(self.banner, new_size)
            self.banner.set_alpha(160) # Un poco transparente
        except:
            self.banner = None

    def show_message(self, text, duration=180, color=(255, 230, 150)):
        self.message = text
        self.message_timer = duration
        self.message_color = color

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.message = ""
        self.menu_anim_t += 1

    def handle_menu_input(self, input_events, joy, just_pressed_start):
        """Maneja la navegación del menú. Retorna un dict con la acción."""
        result = {"action": None, "wave": None}

        # Detectar dirección (event-based = ya debounced)
        up = input_events.get("menu_up", False)
        down = input_events.get("menu_down", False)
        confirm = input_events.get("menu_confirm", False) or just_pressed_start
        back = input_events.get("menu_back", False)

        # Joystick hat/dpad (event-based via axes threshold)
        if joy:
            try:
                # Usar hat si disponible
                if joy.get_numhats() > 0:
                    hat = joy.get_hat(0)
                    if not hasattr(self, '_last_hat'):
                        self._last_hat = (0, 0)
                    if hat[1] == 1 and self._last_hat[1] != 1:
                        up = True
                    elif hat[1] == -1 and self._last_hat[1] != -1:
                        down = True
                    self._last_hat = hat

                # Stick con debounce
                axis_y = joy.get_axis(1)
                if not hasattr(self, '_last_axis_y'):
                    self._last_axis_y = 0.0
                if axis_y < -0.5 and self._last_axis_y >= -0.5:
                    up = True
                elif axis_y > 0.5 and self._last_axis_y <= 0.5:
                    down = True
                self._last_axis_y = axis_y

                if joy.get_button(1):  # B = back
                    back = True
            except:
                pass

        if self.sub_menu is None:
            # Menú principal
            if up:
                self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
            elif down:
                self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
            elif confirm:
                if self.menu_selection == 0:
                    result["action"] = "play"
                elif self.menu_selection == 1:
                    result["action"] = "tutorial"
                elif self.menu_selection == 2:
                    self.sub_menu = "wave_select"
                    self.wave_selection = 0
                elif self.menu_selection == 3:
                    self.sub_menu = "controls"
        elif self.sub_menu == "wave_select":
            if up:
                self.wave_selection = (self.wave_selection - 1) % len(self.wave_labels)
            elif down:
                self.wave_selection = (self.wave_selection + 1) % len(self.wave_labels)
            elif confirm:
                result["action"] = "play_wave"
                result["wave"] = self.wave_selection
            elif back:
                self.sub_menu = None
        elif self.sub_menu == "controls":
            if back or confirm:
                self.sub_menu = None

        return result

    def draw(self, surface, player_hp, max_hp, player_mana, max_mana, player_super, max_super, wave, score, game_state, continue_timer=0, best_score=0, best_wave=0, combo_count=0):
        bar_x, bar_y = 20, 20

        S = getattr(self, "scale", 2)
        # Dibujar bola roja de vida por DETRÁS del frame
        if self.red_ball and max_hp > 0:
            ratio = player_hp / max_hp
            h = int(self.red_ball.get_height() * ratio)
            if h > 0:
                sub = self.red_ball.subsurface((0, self.red_ball.get_height() - h, self.red_ball.get_width(), h))
                bx = bar_x + (2 * S) # offset x * scale
                by = bar_y + (5 * S) + (self.red_ball.get_height() - h)
                surface.blit(sub, (bx, by))

        # Barra Azul (Mana) - Slot inferior con líneas
        if self.blue_bar and max_mana > 0:
            ratio_mana = player_mana / max_mana
            w = int(self.blue_bar.get_width() * ratio_mana)
            if w > 0:
                sub = self.blue_bar.subsurface((0, 0, w, self.blue_bar.get_height()))
                bb_x = bar_x + (69 * S)
                bb_y = bar_y + (35 * S)
                surface.blit(sub, (bb_x, bb_y))

        # Barra Amarilla (Super) - Slot superior liso
        if self.yellow_bar and max_super > 0:
            ratio_super = player_super / max_super
            w = int(self.yellow_bar.get_width() * ratio_super)
            if w > 0:
                sub = self.yellow_bar.subsurface((0, 0, w, self.yellow_bar.get_height()))
                bb_x = bar_x + (62 * S)
                bb_y = bar_y + (20 * S)
                surface.blit(sub, (bb_x, bb_y))

        # Dibujar el marco de la barra de vida POR ENCIMA
        if self.hp_bar_frame:
            surface.blit(self.hp_bar_frame, (bar_x, bar_y))

        # Oleada
        wave_str = f"OLEADA {wave + 1}"
        # Sombra doble para profundidad
        wave_shadow1 = self.font.render(wave_str, True, (0, 0, 0))
        wave_shadow2 = self.font.render(wave_str, True, (40, 20, 80))
        sw, sh = wave_shadow1.get_width(), wave_shadow1.get_height()
        surface.blit(wave_shadow1, (SCREEN_WIDTH // 2 - sw // 2 + 3, 15))
        surface.blit(wave_shadow2, (SCREEN_WIDTH // 2 - sw // 2 + 1, 13))
        # Texto principal (Degradado sutil simulado con dos pasadas)
        wave_text = self.font.render(wave_str, True, (200, 150, 255))
        surface.blit(wave_text, (SCREEN_WIDTH // 2 - sw // 2, 12))

        # Puntuación
        score_str = f"Puntos: {score}"
        # Sombra doble
        score_shadow1 = self.font.render(score_str, True, (0, 0, 0))
        score_shadow2 = self.font.render(score_str, True, (80, 40, 0))
        ssw = score_shadow1.get_width()
        surface.blit(score_shadow1, (SCREEN_WIDTH - ssw - 17, 15))
        surface.blit(score_shadow2, (SCREEN_WIDTH - ssw - 19, 13))
        # Texto principal
        score_text = self.font.render(score_str, True, (255, 200, 50))
        surface.blit(score_text, (SCREEN_WIDTH - ssw - 20, 12))

        # Mejor puntuación
        if best_score > 0:
            best_str = f"Mejor: {best_score} | Oleada {best_wave}"
            best_shadow = self.font_small.render(best_str, True, (20, 10, 0))
            surface.blit(best_shadow, (SCREEN_WIDTH - best_shadow.get_width() - 19, 40))
            best_text = self.font_small.render(best_str, True, (200, 180, 140))
            surface.blit(best_text, (SCREEN_WIDTH - best_text.get_width() - 20, 38))

        # Texto de HP numérico (fuera del círculo, más legible)
        hp_text = self.font_small.render(f"{player_hp}/{max_hp}", True, (255, 255, 255))
        surface.blit(hp_text, (bar_x + 10, bar_y + 45 * S))
        
        # Contador de combo
        if combo_count > 0:
            combo_color = (255, 200, 100) if combo_count < 3 else (255, 100, 100)  # Naranja -> Rojo en combo
            combo_text = self.font.render(f"COMBO x{combo_count}", True, combo_color)
            surface.blit(combo_text, (bar_x + 10, bar_y + 70 * S))

        # Banner Universidad (inferior derecha)
        if self.banner:
            bx = SCREEN_WIDTH - self.banner.get_width() - 10
            by = SCREEN_HEIGHT - self.banner.get_height() - 10
            surface.blit(self.banner, (bx, by))

        # Mensaje central
        if self.message:
            alpha = 255
            if self.message_timer < 30:
                alpha = int(255 * self.message_timer / 30)
            msg_surf = self.font_big.render(self.message, True, self.message_color)
            msg_surf.set_alpha(alpha)
            mx = SCREEN_WIDTH // 2 - msg_surf.get_width() // 2
            my = SCREEN_HEIGHT // 3
            surface.blit(msg_surf, (mx, my))

        # Pantallas de estado
        if game_state == "menu":
            self._draw_menu(surface, best_score, best_wave)
        elif game_state == "wave_intro":
            pass
        elif game_state == "paused":
            self._draw_pause(surface)
        elif game_state == "gameover":
            self._draw_gameover(surface, continue_timer, score, best_score)
        elif game_state == "victory":
            self._draw_victory(surface, score)

    def _draw_menu(self, surface, best_score=0, best_wave=0):
        # Fondo
        if self.menu_bg:
            surface.blit(self.menu_bg, (0, 0))
        else:
            for i in range(SCREEN_HEIGHT):
                r = max(0, min(255, 8 + i // 50))
                g = max(0, min(255, 5 + i // 80))
                b = max(0, min(255, 18 + i // 40))
                pygame.draw.line(surface, (r, g, b), (0, i), (SCREEN_WIDTH, i))

        # Overlay oscuro sutil
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        t = self.menu_anim_t

        # ── Título ──
        glow = int(200 + 55 * math.sin(t / 60.0))
        title_color = (glow, int(glow * 0.85), int(glow * 0.5))
        title = self.font_title.render("COLISEO DE LAS", True, title_color)
        title2 = self.font_title.render("SOMBRAS", True, title_color)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
        surface.blit(title2, (SCREEN_WIDTH // 2 - title2.get_width() // 2, 130))

        # Línea decorativa bajo el título
        line_w = 400
        line_x = SCREEN_WIDTH // 2 - line_w // 2
        pygame.draw.line(surface, (150, 120, 80), (line_x, 210), (line_x + line_w, 210), 2)

        # Versión
        ver_txt = self.font_small.render("v1.0.0", True, (120, 110, 100))
        surface.blit(ver_txt, (SCREEN_WIDTH - ver_txt.get_width() - 20, 20))

        if self.sub_menu is None:
            self._draw_main_menu_options(surface, t, best_score, best_wave)
        elif self.sub_menu == "wave_select":
            self._draw_wave_select(surface, t)
        elif self.sub_menu == "controls":
            self._draw_controls_screen(surface)

    def _draw_main_menu_options(self, surface, t, best_score, best_wave):
        """Dibuja las opciones principales del menú."""
        start_y = 280
        for i, option in enumerate(self.menu_options):
            is_selected = (i == self.menu_selection)

            # Animación de selección
            offset_x = 0
            if is_selected:
                offset_x = int(8 * math.sin(t / 15.0))

            # Colores
            if is_selected:
                color = (255, 220, 100)
                bg_alpha = 60
            else:
                color = (180, 170, 160)
                bg_alpha = 20

            # Fondo del item
            item_w = 500
            item_h = 50
            item_x = SCREEN_WIDTH // 2 - item_w // 2 + offset_x
            item_y = start_y + i * 70

            bg_surf = pygame.Surface((item_w, item_h), pygame.SRCALPHA)
            if is_selected:
                # Gradiente dorado
                for dy in range(item_h):
                    alpha = int(bg_alpha * (1 - dy / item_h))
                    pygame.draw.line(bg_surf, (200, 170, 80, alpha), (0, dy), (item_w, dy))
                # Bordes
                pygame.draw.rect(bg_surf, (255, 200, 80, 120), (0, 0, item_w, item_h), 2)
            else:
                bg_surf.fill((40, 35, 50, bg_alpha))
                pygame.draw.rect(bg_surf, (80, 70, 90, 60), (0, 0, item_w, item_h), 1)

            surface.blit(bg_surf, (item_x, item_y))

            # Indicador de selección
            if is_selected:
                arrow = self.font_menu.render("►", True, (255, 200, 80))
                surface.blit(arrow, (item_x - 35, item_y + 5))

            # Texto
            txt = self.font_menu.render(option, True, color)
            surface.blit(txt, (item_x + item_w // 2 - txt.get_width() // 2, item_y + 8))

        # ── Mejor puntuación ──
        if best_score > 0:
            record_y = start_y + len(self.menu_options) * 70 + 30
            # Panel de records
            panel_w = 400
            panel_h = 60
            panel_x = SCREEN_WIDTH // 2 - panel_w // 2
            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel_surf.fill((20, 15, 30, 150))
            pygame.draw.rect(panel_surf, (100, 80, 120, 100), (0, 0, panel_w, panel_h), 1)
            surface.blit(panel_surf, (panel_x, record_y))

            trophy = self.font.render("🏆", True, (255, 220, 100))
            surface.blit(trophy, (panel_x + 15, record_y + 8))

            rec1 = self.font.render(f"Mejor Puntuación: {best_score}", True, (255, 220, 100))
            surface.blit(rec1, (panel_x + 50, record_y + 5))
            rec2 = self.font_small.render(f"Mejor Oleada: {best_wave}", True, (180, 160, 140))
            surface.blit(rec2, (panel_x + 50, record_y + 32))

        # ── Instrucciones de navegación ──
        nav_y = SCREEN_HEIGHT - 60
        nav = self.font_small.render("W/S o ↑/↓ para navegar  •  ENTER/A para seleccionar", True, (130, 120, 110))
        surface.blit(nav, (SCREEN_WIDTH // 2 - nav.get_width() // 2, nav_y))

    def _draw_wave_select(self, surface, t):
        """Dibuja la pantalla de selección de oleada/jefe."""
        # Título
        title = self.font_big.render("SELECCIONAR OLEADA", True, (255, 220, 100))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 240))

        # Línea decorativa
        line_w = 350
        line_x = SCREEN_WIDTH // 2 - line_w // 2
        pygame.draw.line(surface, (150, 120, 80), (line_x, 295), (line_x + line_w, 295), 1)

        # Lista de oleadas
        visible_count = 6
        start_idx = max(0, self.wave_selection - visible_count // 2)
        end_idx = min(len(self.wave_labels), start_idx + visible_count)
        if end_idx - start_idx < visible_count:
            start_idx = max(0, end_idx - visible_count)

        list_y = 320
        for draw_i, wave_i in enumerate(range(start_idx, end_idx)):
            is_selected = (wave_i == self.wave_selection)
            is_boss = "JEFE" in self.wave_labels[wave_i]

            item_w = 550
            item_h = 45
            item_x = SCREEN_WIDTH // 2 - item_w // 2
            item_y = list_y + draw_i * 55

            # Animación de selección
            offset_x = 0
            if is_selected:
                offset_x = int(6 * math.sin(t / 12.0))
                item_x += offset_x

            bg_surf = pygame.Surface((item_w, item_h), pygame.SRCALPHA)
            if is_selected:
                if is_boss:
                    bg_surf.fill((80, 20, 20, 80))
                    pygame.draw.rect(bg_surf, (255, 80, 80, 150), (0, 0, item_w, item_h), 2)
                else:
                    bg_surf.fill((30, 30, 60, 80))
                    pygame.draw.rect(bg_surf, (200, 180, 100, 150), (0, 0, item_w, item_h), 2)
            else:
                bg_surf.fill((20, 18, 30, 50))
                pygame.draw.rect(bg_surf, (60, 50, 70, 60), (0, 0, item_w, item_h), 1)

            surface.blit(bg_surf, (item_x, item_y))

            # Colores según tipo
            if is_selected:
                text_color = (255, 80, 80) if is_boss else (255, 220, 100)
            else:
                text_color = (180, 100, 100) if is_boss else (160, 155, 150)

            # Indicador
            if is_selected:
                arrow = self.font.render("►", True, text_color)
                surface.blit(arrow, (item_x - 25, item_y + 10))

            # Icono de tipo
            if is_boss:
                icon = self.font.render("💀", True, text_color)
            else:
                icon = self.font.render("⚔", True, text_color)
            surface.blit(icon, (item_x + 12, item_y + 10))

            # Texto
            txt = self.font.render(self.wave_labels[wave_i], True, text_color)
            surface.blit(txt, (item_x + 45, item_y + 12))

        # Scrollbar
        if len(self.wave_labels) > visible_count:
            sb_x = SCREEN_WIDTH // 2 + 290
            sb_h = visible_count * 55
            sb_thumb_h = max(20, sb_h * visible_count // len(self.wave_labels))
            sb_thumb_y = list_y + int((sb_h - sb_thumb_h) * self.wave_selection / max(1, len(self.wave_labels) - 1))
            pygame.draw.rect(surface, (40, 35, 50), (sb_x, list_y, 4, sb_h))
            pygame.draw.rect(surface, (150, 130, 100), (sb_x, sb_thumb_y, 4, sb_thumb_h))

        # Instrucciones
        nav_y = SCREEN_HEIGHT - 60
        nav = self.font_small.render("W/S para navegar  •  ENTER/A para jugar  •  ESC/B para volver", True, (130, 120, 110))
        surface.blit(nav, (SCREEN_WIDTH // 2 - nav.get_width() // 2, nav_y))

    def _draw_controls_screen(self, surface):
        """Dibuja la pantalla de controles."""
        title = self.font_big.render("CONTROLES", True, (255, 220, 100))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 240))

        controls = [
            ("Mover", "A / D", "Stick Izq."),
            ("Saltar", "ESPACIO", "A"),
            ("Atacar", "J", "X"),
            ("Dash", "K", "B"),
            ("Parry", "U", "Y"),
            ("Magia", "L", "RB"),
            ("Curar", "H", "LB (mantener)"),
            ("Super", "-", "LB (cargado)"),
            ("Pausa", "ENTER", "START"),
        ]

        # Panel
        panel_w = 600
        panel_x = SCREEN_WIDTH // 2 - panel_w // 2
        panel_y = 300

        # Encabezados
        headers = [("ACCIÓN", panel_x + 20), ("TECLADO", panel_x + 200), ("MANDO", panel_x + 400)]
        for text, hx in headers:
            h_txt = self.font.render(text, True, (200, 180, 140))
            surface.blit(h_txt, (hx, panel_y))

        pygame.draw.line(surface, (100, 80, 60), (panel_x, panel_y + 28), (panel_x + panel_w, panel_y + 28), 1)

        for i, (action, key, joy_btn) in enumerate(controls):
            y = panel_y + 38 + i * 32
            row_color = (180, 175, 170) if i % 2 == 0 else (160, 155, 150)

            # Fondo alternado
            if i % 2 == 0:
                row_bg = pygame.Surface((panel_w, 28), pygame.SRCALPHA)
                row_bg.fill((40, 35, 50, 40))
                surface.blit(row_bg, (panel_x, y - 2))

            a_txt = self.font_small.render(action, True, row_color)
            surface.blit(a_txt, (panel_x + 20, y))

            k_txt = self.font_small.render(key, True, (150, 200, 255))
            surface.blit(k_txt, (panel_x + 200, y))

            j_txt = self.font_small.render(joy_btn, True, (150, 255, 150))
            surface.blit(j_txt, (panel_x + 400, y))

        # Instrucciones
        nav = self.font_small.render("ENTER/A o ESC/B para volver", True, (130, 120, 110))
        surface.blit(nav, (SCREEN_WIDTH // 2 - nav.get_width() // 2, SCREEN_HEIGHT - 60))

    def _draw_pause(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        pause_txt = self.font_title.render("PAUSA", True, (255, 255, 255))
        surface.blit(pause_txt, (SCREEN_WIDTH // 2 - pause_txt.get_width() // 2, 250))
        
        info = self.font.render("Presiona START o ENTER para continuar", True, (200, 200, 200))
        surface.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 350))

    def _draw_gameover(self, surface, continue_timer=0, score=0, best_score=0):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((40, 5, 5, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("HAS CAÍDO", True, (255, 80, 80))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))

        # Mostrar puntuación obtenida
        score_txt = self.font_big.render(f"Puntuación: {score}", True, (255, 200, 100))
        surface.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2, 260))

        if best_score > 0:
            best_txt = self.font.render(f"Mejor: {best_score}", True, (180, 160, 140))
            surface.blit(best_txt, (SCREEN_WIDTH // 2 - best_txt.get_width() // 2, 310))

        if continue_timer > 0:
            secs = int(continue_timer) + 1
            color = (100, 255, 100) if secs > 5 else (255, 100, 100)
            cont_txt = self.font_big.render(f"CONTINUAR?  {secs}s", True, color)
            surface.blit(cont_txt, (SCREEN_WIDTH // 2 - cont_txt.get_width() // 2, 370))

            sub = self.font.render("Presiona ENTER o START para continuar", True, (200, 180, 180))
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 440))
        else:
            sub = self.font_big.render("Presiona ENTER o START", True, (200, 180, 180))
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 380))
            sub2 = self.font.render("para volver al menú", True, (160, 150, 140))
            surface.blit(sub2, (SCREEN_WIDTH // 2 - sub2.get_width() // 2, 430))

    def _draw_victory(self, surface, score=0):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 20, 40, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("¡VICTORIA!", True, (255, 220, 100))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 220))

        sub = self.font_big.render("¡Has conquistado el Coliseo!", True, (180, 200, 255))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 310))

        score_txt = self.font_big.render(f"Puntuación Final: {score}", True, (255, 220, 100))
        surface.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2, 370))

        sub2 = self.font.render("Presiona ENTER o START para jugar de nuevo", True, (160, 160, 180))
        surface.blit(sub2, (SCREEN_WIDTH // 2 - sub2.get_width() // 2, 440))
