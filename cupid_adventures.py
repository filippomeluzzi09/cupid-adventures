#Manila Baldini 
#Maria Fontana
#Filippo Meluzzi

# Cupid Adventures 3D - Full Leaderboard & Menu Button Edition ❤️
# pip install pygame moderngl numpy

import pygame
import random
import math
import moderngl
import array
import numpy as np
import os

pygame.init()
pygame.mixer.init()

# =========================================
# FINESTRA ED ENGINE GRAFICO (GPU)
# =========================================
WIDTH = 1400
HEIGHT = 1000

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
pygame.display.set_caption("Cupid Adventures 3D - Complete Leaderboard & Reset System")
clock = pygame.time.Clock()

ctx = moderngl.create_context()

try:
    pop_sound = pygame.mixer.Sound("pop.wav")
except:
    pop_sound = None

font = pygame.font.SysFont("segoeui", 36, bold=True)
medium_font = pygame.font.SysFont("segoeui", 48, bold=True)
big_font = pygame.font.SysFont("segoeui", 110, bold=True)

# =========================================
# PIPELINE SHADER 3D
# =========================================
VERTEX_SHADER_3D = '''
#version 330
in vec2 in_vert;
in vec2 in_texcoord;
out vec2 v_texcoord;
void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    v_texcoord = in_texcoord;
}
'''

FRAGMENT_SHADER_3D = '''
#version 330
uniform sampler2D Texture;
uniform float time;
uniform vec2 light_pos;
in vec2 v_texcoord;
out vec4 f_color;

void main() {
    vec2 clean_uv = v_texcoord;
    vec4 base_color = texture(Texture, clean_uv);
    
    float dist = distance(clean_uv, vec2(light_pos.x / 1400.0, light_pos.y / 1000.0));
    float light_intensity = 0.0;
    if (light_pos.x > 0.0) {
        float flicker = 1.0 + sin(time * 20.0) * 0.1;
        light_intensity = (0.015 / (dist + 0.04)) * flicker;
    }
    vec4 light_color = vec4(1.0, 0.5, 0.6, 0.0) * light_intensity;

    f_color = base_color + light_color;
}
'''

program = ctx.program(vertex_shader=VERTEX_SHADER_3D, fragment_shader=FRAGMENT_SHADER_3D)

render_object = ctx.buffer(array.array('f', [
    -1.0,  1.0,        0.0, 0.0,
    -1.0, -1.0,        0.0, 1.0,
     1.0,  1.0,        1.0, 0.0,
     1.0, -1.0,        1.0, 1.0,
]))
vao = ctx.vertex_array(program, [(render_object, '2f 2f', 'in_vert', 'in_texcoord')])

pygame_surface = pygame.Surface((WIDTH, HEIGHT))

# =========================================
# STATI DI GIOCO, PUNTEGGI E UTENTE
# =========================================
game_state = "LOGIN"
game_mode = "DIFFICILE"
username = ""
leaderboard_data = []

player_x = 150
player_y = HEIGHT // 2
time_elapsed = 0
score = 0  

lives = 3
MAX_LIVES = 5

arrows = []
particles = []
targets = []

# Tasto "Torna al Menu" durante il gameplay
btn_back_to_menu = pygame.Rect(WIDTH - 320, 40, 280, 65)

WHITE, BLACK, GOLD, DEEP_GOLD = (255, 255, 255), (15, 12, 15), (255, 215, 0), (184, 134, 11)
RED_GLOW, DARK_RED = (255, 50, 90), (120, 10, 25)
SKIN_BASE, SKIN_SHADOW = (245, 210, 185), (210, 160, 135)

# =========================================
# GESTIONE FILE CLASSIFICA FORZATA NELLA CARTELLA
# =========================================
# Calcoliamo la cartella esatta in cui si trova questo file di script .py
SCRIPT_DIR = os.path.dirname(os.path.abspath(_file_))
FILE_CLASSIFICA = os.path.join(SCRIPT_DIR, "classifica.txt")

def save_score_to_file():
    global username, score, game_mode
    scores = []
    
    # 1. Se il file esiste, prova a leggerlo riga per riga in modo sicuro
    if os.path.exists(FILE_CLASSIFICA):
        try:
            with open(FILE_CLASSIFICA, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    parts = line.split(" - ")
                    if len(parts) == 2:
                        name = parts[0]
                        # Estrae in modo solido il numero prima della parola "Punti"
                        pt_str = parts[1].replace(" Punti", "").strip()
                        scores.append((name, int(pt_str)))
        except Exception as e:
            print("Avviso lettura vecchia classifica fallita (file corrotto?), resetto. Errore:", e)
            
    # 2. Aggiunge il punteggio del match corrente
    display_name = f"{username} [{game_mode}]"
    scores.append((display_name, score))
    
    # 3. Ordina decrescente in base ai punti (elemento x[1]) e tronca a 5 elementi
    scores.sort(key=lambda x: x[1], reverse=True)
    scores = scores[:5]
    
    # 4. Scrive la nuova classifica nel file txt forzando la posizione
    try:
        with open(FILE_CLASSIFICA, "w", encoding="utf-8") as f:
            for name, pt in scores:
                f.write(f"{name} - {pt} Punti\n")
    except Exception as e:
        print("Errore irreversibile durante il salvataggio su file:", e)

def load_leaderboard():
    global leaderboard_data
    leaderboard_data.clear()
    if os.path.exists(FILE_CLASSIFICA):
        try:
            with open(FILE_CLASSIFICA, "r", encoding="utf-8") as f:
                leaderboard_data = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print("Impossibile caricare la classifica a schermo:", e)

# =========================================
# UTILITY GRAFICHE VETTORIALI
# =========================================
def draw_gradient_rect(surf, c1, c2, rect):
    x, y, w, h = rect
    for yy in range(h):
        alpha = yy / h
        r = int(c1[0] + (c2[0] - c1[0]) * alpha)
        g = int(c1[1] + (c2[1] - c1[1]) * alpha)
        b = int(c1[2] + (c2[2] - c1[2]) * alpha)
        pygame.draw.line(surf, (r, g, b), (x, y + yy), (x + w, y + yy))

def draw_3d_sphere(surf, center, radius, base_color, shadow_color):
    cx, cy = center
    if radius <= 0: return
    for r in range(int(radius), 0, -1):
        alpha = (radius - r) / radius
        lx = cx
        ly = cy - int((radius - r) * 0.15)
        curr_color = (
            int(shadow_color[0] + (base_color[0] - shadow_color[0]) * alpha),
            int(shadow_color[1] + (base_color[1] - shadow_color[1]) * alpha),
            int(shadow_color[2] + (base_color[2] - shadow_color[2]) * alpha)
        )
        pygame.draw.circle(surf, curr_color, (lx, ly), r)

def draw_heart(surf, x, y, size, color, glow_intensity=25):
    if size <= 0: return
    color_rgb = color[:3]
    for r in range(int(size * 2), int(size), -2):
        gl_alpha = int(glow_intensity * (1.0 - (r / (size * 2))))
        glow_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color_rgb, gl_alpha), (r, r), r)
        surf.blit(glow_surf, (int(x - r), int(y - r)), special_flags=pygame.BLEND_RGBA_ADD)

    pygame.draw.circle(surf, color_rgb, (int(x - size * 0.5), int(y - size * 0.5)), int(size * 0.5))
    pygame.draw.circle(surf, color_rgb, (int(x + size * 0.5), int(y - size * 0.5)), int(size * 0.5))
    pygame.draw.polygon(surf, color_rgb, [
        (int(x - size * 1.0), int(y - size * 0.4)),
        (int(x + size * 1.0), int(y - size * 0.4)),
        (int(x), int(y + size * 1.0))
    ])

# =========================================
# CLASSE BERSAGLIO 3D PROPORZIONALE
# =========================================
class Target3D:
    def __init__(self, mode):
        self.mode = mode
        self.x = random.randint(750, 1200)
        self.y = random.randint(250, 550)
        self.z = random.uniform(0.7, 1.4) 
        self.speed_x = random.uniform(2.5, 4.5)
        self.speed_y = 0
        self.dir_x = random.choice([-1, 1])
        self.dir_y = random.choice([-1, 1])
        self.change_timer = 0
        self.walk_cycle = random.uniform(0, 100)

    def move(self):
        self.change_timer -= 1
        self.walk_cycle += 0.15
        
        if score >= 5:
            if self.change_timer <= 0:
                self.speed_y = random.uniform(3.5, 6.5)
                self.speed_x = random.uniform(4.0, 7.5)
                self.dir_x = random.choice([-1, 1])
                self.dir_y = random.choice([-1, 1])
                self.change_timer = random.randint(45, 90)
        else:
            self.speed_y = 0  

        multiplier = 1.5 if (self.mode == "DIFFICILE" and score >= 10) else 1.0

        self.x += self.speed_x * self.dir_x * multiplier
        self.y += self.speed_y * self.dir_y * multiplier

        if self.x < 650 or self.x > 1300: self.dir_x *= -1
        if self.y < 180 or self.y > HEIGHT - 350: self.dir_y *= -1

    def draw(self, surf):
        scale = 1.0 / self.z
        cx, cy = int(self.x), int(self.y)

        shadow_w = int(120 * scale)
        shadow_h = int(30 * scale)
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 45), (0, 0, shadow_w, shadow_h))
        surf.blit(shadow_surf, (cx - shadow_w // 2, HEIGHT - 145))

        pygame.draw.circle(surf, (35, 18, 12), (cx, cy - int(32 * scale)), int(48 * scale))
        draw_3d_sphere(surf, (cx, cy - int(20 * scale)), int(36 * scale), SKIN_BASE, SKIN_SHADOW)
            
        pygame.draw.circle(surf, BLACK, (cx - int(14 * scale), cy - int(24 * scale)), max(1, int(3 * scale)))
        pygame.draw.circle(surf, BLACK, (cx + int(14 * scale), cy - int(24 * scale)), max(1, int(3 * scale)))
        pygame.draw.arc(surf, (160, 50, 50), (cx - int(15 * scale), cy - int(22 * scale), int(30 * scale), int(16 * scale)), math.pi, 0, max(2, int(3 * scale)))

        color_cloth = (230, 70, 60) if score >= 5 else (75, 120, 240)
        pygame.draw.rect(surf, color_cloth, (cx - int(32 * scale), cy + int(20 * scale), int(64 * scale), int(90 * scale)), border_radius=int(14 * scale))
        
        pygame.draw.line(surf, SKIN_BASE, (cx - int(32 * scale), cy + int(35 * scale)), (cx - int(60 * scale), cy + int(75 * scale)), max(2, int(11 * scale)))
        pygame.draw.line(surf, SKIN_BASE, (cx + int(32 * scale), cy + int(35 * scale)), (cx + int(60 * scale), cy + int(75 * scale)), max(2, int(11 * scale)))

        leg_sway = math.sin(self.walk_cycle) * 14 * scale
        pygame.draw.line(surf, (40, 40, 45), (cx - int(16 * scale), cy + int(105 * scale)), (cx - int(16 * scale) + int(leg_sway), cy + int(155 * scale)), max(2, int(12 * scale)))
        pygame.draw.line(surf, (40, 40, 45), (cx + int(16 * scale), cy + int(105 * scale)), (cx + int(16 * scale) - int(leg_sway), cy + int(155 * scale)), max(2, int(12 * scale)))

        draw_heart(surf, cx, cy + int(60 * scale), int(12 * scale), RED_GLOW, glow_intensity=15)

class Particle3D:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.angle = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(4.0, 12.0)
        self.life = random.randint(30, 60)
        self.max_life = self.life
        self.size = random.randint(6, 14)

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed + 1.2
        self.speed *= 0.94
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * (self.life / self.max_life))
        if self.size > 0:
            draw_heart(surf, int(self.x), int(self.y), int(self.size * 0.6), (255, 60, 100, alpha), glow_intensity=10)

def start_game(mode):
    global game_state, game_mode, lives, score, arrows, particles, targets, player_y
    game_mode = mode
    game_state = "PLAYING"
    lives = 3
    score = 0
    player_y = HEIGHT // 2
    arrows.clear()
    particles.clear()
    targets = [Target3D(game_mode) for _ in range(4)]

# =========================================
# ENGINE LOOP CORE PRINCIPALE
# =========================================
running = True
while running:
    clock.tick(60)
    time_elapsed += 1
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            if game_state == "LOGIN":
                if event.key == pygame.K_RETURN:
                    if len(username.strip()) > 0: game_state = "HOME"
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    if len(username) < 15 and event.unicode.isalnum() or event.unicode == ' ':
                        username += event.unicode
            elif game_state == "PLAYING":
                if event.key == pygame.K_SPACE:
                    arrows.append([player_x + 65, player_y + 12])

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == "HOME":
                if btn_difficile.collidepoint(mouse_pos): start_game("DIFFICILE")
                elif btn_infinita.collidepoint(mouse_pos): start_game("INFINITA")
            elif game_state == "PLAYING":
                if btn_back_to_menu.collidepoint(mouse_pos):
                    game_state = "HOME"
            elif game_state in ["VICTORY", "GAME_OVER"]:
                game_state = "HOME"

    pygame_surface.fill((0, 0, 0))

    draw_gradient_rect(pygame_surface, (255, 175, 200), (255, 235, 245), (0, 0, WIDTH, HEIGHT))
    draw_gradient_rect(pygame_surface, (100, 190, 110), (60, 130, 70), (0, HEIGHT - 160, WIDTH, 160))

    random.seed(1337)
    for i in range(0, WIDTH, 6):
        h = random.randint(15, 30)
        pygame.draw.line(pygame_surface, (45, 110, 55), (i, HEIGHT - 160), (i + 2, HEIGHT - 160 - h), 2)
    random.seed()

    current_light_x, current_light_y = -100.0, -100.0