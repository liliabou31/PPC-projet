import pygame
import sys

def run_display(queue):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Écosystème PPC - Simulation")
    clock = pygame.time.Clock()

    while True:
        # 1. Quitter proprement
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # 2. Lire les dernières données
        data = None
        while not queue.empty():
            data = queue.get()
            if data == "STOP":
                pygame.quit()
                return

        if data:
            # Fond : Vert sombre (Herbe) ou Marron (Sécheresse)
            bg_color = (60, 40, 30) if data["drought"] else (20, 50, 20)
            screen.fill(bg_color)

            # Dessiner la jauge d'herbe en haut
            pygame.draw.rect(screen, (0, 255, 0), (10, 10, data["grass"] * 2, 15))

            # 3. Dessiner les PROIES (Cercles bleus)
            for x, y in data["preys_coords"]:
                pygame.draw.circle(screen, (0, 200, 255), (int(x), int(y)), 6)

            # 4. Dessiner les PRÉDATEURS (Cercles rouges)
            for x, y in data["preds_coords"]:
                pygame.draw.circle(screen, (255, 50, 50), (int(x), int(y)), 10)

            pygame.display.flip()
        
        clock.tick(30) # 30 FPS pour la fluidité