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

class Prey:
    def __init__(self, shared_data, lock):
        self.energy = 50
        self.state = "passive"
        self.shared = shared_data
        self.lock = lock
        self.alive = True
        self.pid = os.getpid()
        self.shared["prey_states"][self.pid] = self.state
        self.x = random.randint(50, 750) # Position de départ
        self.y = random.randint(50, 550)
        # On stocke maintenant (x, y, état)
        self.shared["prey_states"][self.pid] = (self.x, self.y, self.state)

    def connect_to_env(self):
        """ Se connecte au socket de 'env' pour signaler son arrivée """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.sendall(b"new_prey") # On envoie un simple message texte
        except ConnectionRefusedError:
            print("Erreur : Le processus 'env' n'est pas prêt.")
            return

    def update_state(self):
        """ Change l'état de manière déterministe """
        old_state = self.state
        if self.energy < H:
            self.state = "active"
        elif self.energy > H + 10:
            self.state = "passive"
        
        # 2. Mettre à jour le dictionnaire partagé si l'état change
        if old_state != self.state:
            self.shared["prey_states"][self.pid] = self.state

    def live_one_cycle(self):
        # auto-vérifcation afin d'éviter les proies zombies 
        # Faire bouger l'animal
        self.x += random.randint(-5, 5)
        self.y += random.randint(-5, 5)
        # Garder dans les limites de l'écran
        self.x = max(10, min(790, self.x))
        self.y = max(10, min(590, self.y))
        
        # Mettre à jour la mémoire partagée avec la position
        with self.lock:
            if self.pid in self.shared["prey_states"]:
                self.shared["prey_states"][self.pid] = (self.x, self.y, self.state)
                
        with self.lock:
            if self.pid not in self.shared["prey_states"]:
                print(f"[PROIE {self.pid}] Je ne suis plus dans le dictionnaire, je m'arrête.")
                self.alive = False
                return 

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
                # Si la proie est encore là (pas mangée par un prédateur entre temps)
                if self.pid in self.shared["prey_states"]:
                    del self.shared["prey_states"][self.pid]
                    # On s'assure de ne pas descendre sous 0
                    if self.shared["preys"].value > 0:
                        self.shared["preys"].value -= 1
                    print(f"[PROIE {self.pid}] morte de faim.")

    def reproduce(self):
        self.energy -= 40 
        new_prey_proc = mp.Process(target=run_prey, args=(self.shared, self.lock))
        new_prey_proc.start()
        print(f"[PROIE {os.getpid()}] s'est reproduite !")


def run_prey(shared, lock):
    prey = Prey(shared, lock)

    while prey.alive:
        prey.live_one_cycle()
        time.sleep(0.5)