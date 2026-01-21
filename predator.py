import multiprocessing as mp
import time
import socket
import random
import os

# Seuils 
H = 30  # Seuil de faim (devient active en dessous)
R = 80  # Seuil de reproduction (au-dessus)

HOST = "localhost"
PORT = 6666

class Predator:
    def __init__(self, shared_data, lock):
        self.energy = 50
        self.state = "passive"
        self.shared = shared_data
        self.lock = lock
        self.alive = True
        self.x = random.randint(0, 100)
        self.y = random.randint(0, 100)

    def connect_to_env(self):
        """ Se connecte au socket de 'env' pour signaler son arrivée """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.sendall(b"new_predator") # On envoie un simple message texte
        except ConnectionRefusedError:
            print("Erreur : Le processus 'env' n'est pas prêt.")
            return

    def update_state(self):
        """ Change l'état de manière déterministe selon l'énergie """
        if self.energy < H:
            self.state = "active"
        elif self.energy > H + 10: # On redevient passif quand on a assez mangé
            self.state = "passive"

    def predator_eats(self): 
        with self.lock:
            # Le prédateur regarde la liste des clés (PIDs)
            for pid, state in self.shared["prey_states"].items():
                if state == "active":
                    # Il a trouvé une proie active !
                    del self.shared["prey_states"][pid] # Il supprime cette proie spécifique
                    self.shared["preys"].value -= 1
                    self.energy += 20
                    print(f"J'ai mangé la proie n°{pid}")
                    break

    def live_one_cycle(self):

        # 1. Le mouvement au hasard
        self.x += random.randint(-2, 2) # Il se déplace de -2 à +2 pixels
        self.y += random.randint(-2, 2)

        # 2. Sécurité : on ne sort pas du monde (0 à 100)
        # Si x devient -1, max(0, -1) renvoie 0. Si x devient 105, min(100, 105) renvoie 100.
        self.x = max(0, min(100, self.x))
        self.y = max(0, min(100, self.y))

        # 3. La Mise à jour CRUCIALE pour Pygame
        # On écrit dans la Shared Memory pour que 'env.py' puisse lire la position
        with self.lock:
            # On stocke un tuple ((x, y), état)
            self.shared["predator_states"][os.getpid()] = ((self.x, self.y), "active")

        # 1. L'énergie baisse naturellement
        self.energy -= 1
        
        # 2. Mise à jour de l'état (Faim ?)
        self.update_state()

        # 3. Action : Manger si active
        if self.state == "active":
            self.predator_eats()

        # 4. Reproduction
        if self.energy > R:
            self.reproduce()

        # 5. Mort
        if self.energy <= 0:
            self.alive = False
            with self.lock:
                if self.shared["predators"].value > 0:
                    self.shared["predators"].value -= 1
            print(f"[PREDATEUR {os.getpid()}] est morte de faim.")

    def reproduce(self):
        self.energy -= 40 
        new_predator_proc = mp.Process(target=run_predator, args=(self.shared, self.lock))
        new_predator_proc.start()
        print(f"[PREDATEUR {os.getpid()}] s'est reproduite !")


# MAIN
def run_predator(shared, lock):
    predator = Predator(shared, lock)

    while predator.alive:
        predator.live_one_cycle()
        time.sleep(0.5)

