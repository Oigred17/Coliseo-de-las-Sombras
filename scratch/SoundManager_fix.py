class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        # Load important sounds
        try:
            self.sounds["attack"] = pygame.mixer.Sound("Efectos de sonido/SFX/07_human_atk_sword_1.wav")
            self.sounds["dash"] = pygame.mixer.Sound("Efectos de sonido/SFX/15_human_dash_1.wav")
            self.sounds["damage"] = pygame.mixer.Sound("Efectos de sonido/SFX/11_human_damage_1.wav")
            self.sounds["jump"] = pygame.mixer.Sound("Efectos de sonido/SFX/12_human_jump_1.wav")
            self.sounds["enemy_hit"] = pygame.mixer.Sound("Efectos de sonido/SFX/26_sword_hit_1.wav")
            self.sounds["victory"] = pygame.mixer.Sound("Efectos de sonido/SFX/10_human_special_atk_1.wav")
            self.sounds["parry"] = pygame.mixer.Sound("Efectos de sonido/SFX/26_sword_hit_1.wav")
            self.sounds["boss_arrival"] = pygame.mixer.Sound("Efectos de sonido/SFX/18_orc_charge.wav")
            self.sounds["cast"] = pygame.mixer.Sound("Efectos de sonido/SFX/08_human_charge_1.wav")
            self.sounds["charged"] = pygame.mixer.Sound("Efectos de sonido/SFX/09_human_charging_1_loop.wav")
            
            # Music
            pygame.mixer.music.load("Efectos de sonido/Music/Goblins_Dance_(Battle).wav")
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play(-1) # Forzar música al inicio
        except Exception as e:
            print(f"No se pudieron cargar los sonidos: {e}")

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].set_volume(0.8)
            self.sounds[name].play()

    def play_music(self):
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
        except:
            pass
