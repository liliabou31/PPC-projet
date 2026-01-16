import time
import socket
import random
import os

# Seuils 
H = 30  # Seuil de faim (devient active en dessous)
R = 80  # Seuil de reproduction (au-dessus)

class Prey:
    def __init__(self, shared_data, lock):
        self.energy = 50 # Énergie initiale
        self.state = "passive"
        self.shared = shared_data # Accès à la mémoire partagée
        self.lock = lock
        self.alive = True

    def connect_to_env(self):
        """ Se connecte au socket de 'env' pour signaler son arrivée """
        # À implémenter avec la bibliothèque socket
        pass

    def update_state(self):
        """ Change l'état de manière déterministe selon l'énergie """
        if self.energy < H:
            self.state = "active"
        elif self.energy > H + 10: # On redevient passif quand on a assez mangé
            self.state = "passive"

    def live_one_cycle(self):
        # 1. L'énergie baisse naturellement
        self.energy -= 1
        
        # 2. Mise à jour de l'état (Faim ?)
        self.update_state()

        # 3. Action : Manger si active
        if self.state == "active":
            with self.lock:
                if self.shared["grass"].value > 0:
                    self.shared["grass"].value -= 1
                    self.energy += 10
                    print(f"[PROIE {os.getpid()}] Mange. Énergie : {self.energy}")

        # 4. Reproduction
        if self.energy > R:
            self.reproduce()

        # 5. Mort
        if self.energy <= 0:
            self.alive = False
            with self.lock:
                self.shared["preys"].value -= 1
            print(f"[PROIE {os.getpid()}] Est morte de faim.")

    def reproduce(self):
        # Logique pour lancer un nouveau processus Prey
        self.energy -= 40 # La reproduction coûte de l'énergie
        # Ici, il faudrait spawn un nouveau processus
        pass

# Cette fonction serait appelée par le processus principal
def run_prey(shared, lock):
    prey = Prey(shared, lock)
    
    # Signaler l'arrivée au compteur global
    with lock:
        shared["preys"].value += 1
    
    while prey.alive:
        prey.live_one_cycle()
        time.sleep(0.5) # Vitesse de la simulation