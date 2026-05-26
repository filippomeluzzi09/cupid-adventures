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