import pygame
import sys

def run_display(queue):
    pygame.init()
    # Configuration de la fenêtre
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simulation Écosystème - PPC")
    clock = pygame.time.Clock()

    while True:
        # 1. Gestion des événements (pour pouvoir fermer la fenêtre)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # 2. Récupération des données (On vide la queue pour avoir le dernier état)
        stats = None
        while not queue.empty():
            stats = queue.get()

        if stats:
            # Fond d'écran (Rougeâtre si sécheresse, vert sinon)
            bg_color = (200, 100, 100) if stats.get("drought") else (30, 30, 30)
            screen.fill(bg_color)

            # Dessiner l'herbe (Barre en bas par exemple)
            grass_level = stats.get("grass", 0)
            pygame.draw.rect(screen, (0, 255, 0), (10, HEIGHT - 20, grass_level * 5, 10))

            # 3. DESSINER LES PROIES (Points bleus)
            for pos in stats.get("preys_coords", []):
                # On multiplie par 8 si ton monde fait 100x100 pour remplir l'écran 800x600
                pygame.draw.circle(screen, (0, 150, 255), (int(pos[0]*8), int(pos[1]*6)), 5)

            # 4. DESSINER LES PRÉDATEURS (Points rouges)
            for pos in stats.get("preds_coords", []):
                pygame.draw.circle(screen, (255, 50, 50), (int(pos[0]*8), int(pos[1]*6)), 8)

            pygame.display.flip() # Mise à jour de l'affichage
        
        clock.tick(30) # 30 FPS pour ne pas surcharger le CPU