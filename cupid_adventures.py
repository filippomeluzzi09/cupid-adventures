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