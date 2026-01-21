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
        self.shared = shared_data
        self.lock = lock
        self.energy = 50
        self.state = "passive"
        self.alive = True
        self.pid = os.getpid()
        self.x = random.randint(50, 750) # Position de départ
        self.y = random.randint(50, 550)
        with self.lock:
        # On stocke maintenant (x, y, état)
            self.shared["predator_states"][self.pid] = (self.x, self.y, self.state)

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
            # On transforme en liste pour figer la vue du dictionnaire
            items = list(self.shared["prey_states"].items())
            
            for pid, state in items:
                if state == "active":
                    # On vérifie si la proie existe encore ET si le compteur est positif
                    if pid in self.shared["prey_states"] and self.shared["preys"].value > 0:
                        del self.shared["prey_states"][pid]
                        self.shared["preys"].value -= 1
                        self.energy += 20
                        print(f"J'ai mangé la proie n°{pid}. Restantes: {self.shared['preys'].value}")
                        return # On sort après avoir mangé une seule proie

    def live_one_cycle(self):
        # Faire bouger l'animal
        self.x += random.randint(-5, 5)
        self.y += random.randint(-5, 5)
        # Garder dans les limites de l'écran
        self.x = max(10, min(790, self.x))
        self.y = max(10, min(590, self.y))
        
        # Mettre à jour la mémoire partagée avec la position
        with self.lock:
            if self.pid in self.shared["predator_states"]:
                self.shared["predator_states"][self.pid] = (self.x, self.y, self.state)

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