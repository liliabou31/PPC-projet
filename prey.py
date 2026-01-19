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
        if self.energy < H:
            self.shared["prey_states"][os.getpid()] = "active"
        elif self.energy > H + 10:
            self.shared["prey_states"][os.getpid()] = "passive"

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
            print(f"[PROIE {os.getpid()}] est morte de faim.")

    def reproduce(self):
        self.energy -= 40 
        new_prey_proc = mp.Process(target=run_prey, args=(self.shared, self.lock))
        new_prey_proc.start()
        print(f"[PROIE {os.getpid()}] s'est reproduite !")


# MAIN
def run_prey(shared, lock):
    prey = Prey(shared, lock)

    prey.connect_to_env()

    while prey.alive:
        prey.live_one_cycle()
        time.sleep(0.5)
