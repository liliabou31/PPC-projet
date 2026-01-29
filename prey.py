import multiprocessing as mp
import time
import socket
import random
import os
import math  # <--- Crucial pour math.sqrt

# Seuils 
H = 30  
R = 60
HOST = "localhost"
PORT = 6666

class Prey:
    def __init__(self, shared_data, lock):
        self.energy = 40
        self.state = "active"
        self.shared = shared_data
        self.lock = lock
        self.alive = True
        self.pid = os.getpid()
        self.x = random.uniform(0, 100)
        self.y = random.uniform(0, 100)
        self.vision_radius = 50
        self.target_grass_index = None        
        with self.lock:
            self.shared["prey_states"][self.pid] = self.state
            self.shared["prey_positions"][self.pid] = (self.x, self.y)

    def find_nearest_grass(self):
        grass_positions = self.shared["static_grass_pos"]
        occupied_grass = self.shared["locked_grass"] 
        best_index = None
        max_dist = float("inf")
                
        for i in range(self.shared["grass"].value):
            if i not in occupied_grass and self.shared["grass_states"][i] == True: 
                pos = grass_positions[i]
                dist = abs(self.x - pos[0])+ abs(self.y - pos[1])
                if dist < max_dist:
                    max_dist = dist
                    best_index = i
                
        if best_index is not None:
            self.shared["locked_grass"][best_index] = self.pid
            self.target_grass_index = best_index

    def direction_vers(self, cible):
        px, py = self.x, self.y
        hx, hy = cible
        directions = []

        if hx < px: directions.append((-1, 0))
        if hx > px: directions.append((1, 0))
        if hy < py: directions.append((0, -1))
        if hy > py: directions.append((0, 1))
        if len(directions) == 2:
            directions.append((directions[0][0], directions[1][1]))

        if not directions:  
            return

        dx, dy = random.choice(directions)
        x, y = self.x, self.y

        self.x, self.y = min(max(0, x + dx), 100 - 1), min(max(0, y + dy), 100 - 1)
        

    def deplacement_proie(self):
            target_reached = False

            if self.state == 'active':
                if self.target_grass_index is None:
                    self.find_nearest_grass()
                
                if self.target_grass_index is not None:
                    #if self.shared["grass_states"][self.target_grass_index] == True:
                    cible_pos = self.shared["static_grass_pos"][self.target_grass_index]
                    #else:
                    #   cible_pos = None
                    #  self.target_grass_index = None 

                    if cible_pos:
                        self.direction_vers(cible_pos)
                        target_reached = True
                        
                        dist = abs(self.x - cible_pos[0]) + abs(self.y - cible_pos[1])
                        if dist < 1.5: 
                            self.eat()
                            self.target_grass_index = None
        
            if not target_reached:
                valeur = random.randint(1, 8)
                dx, dy = 0, 0
                if valeur == 1: dx = 1
                elif valeur == 2: dx = -1
                elif valeur == 3: dy = 1
                elif valeur == 4: dy = -1
                elif valeur == 5: dx, dy = 1, 1
                elif valeur == 6: dx, dy = 1, -1
                elif valeur == 7: dx, dy = -1, 1
                elif valeur == 8: dx, dy = -1, -1
                
                self.x = min(max(self.x + dx, 0), 99)
                self.y = min(max(self.y + dy, 0), 99)

            self.shared["prey_positions"][self.pid] = (self.x, self.y)


    def eat(self):
        idx = self.target_grass_index
        if idx < len(self.shared["grass_states"]):
            self.shared["grass_states"][idx] = False
            self.energy += 25
            #if idx in self.shared["locked_grass"]:
            del self.shared["locked_grass"][idx]
        else:
            #if idx in self.shared["locked_grass"]:
            del self.shared["locked_grass"][idx]

    def update_state(self):
        old_state = self.state
        if self.energy < H:
            self.state = "active"
        elif self.energy > H + 15:
            self.state = "passive"
        
        if old_state != self.state:
            self.shared["prey_states"][self.pid] = self.state

    def die(self, reason):
        self.alive = False
        if self.pid in self.shared["prey_states"]: del self.shared["prey_states"][self.pid]
        if self.pid in self.shared["prey_positions"]: del self.shared["prey_positions"][self.pid]
        if self.target_grass_index is not None:
            if self.target_grass_index in self.shared["locked_grass"]:
                if self.shared["locked_grass"][self.target_grass_index] == self.pid:
                    del self.shared["locked_grass"][self.target_grass_index]
            
        if self.shared["preys"].value > 0:
            self.shared["preys"].value -= 1
        print(f"[PROIE {self.pid}] est morte ({reason}).")

    def reproduce(self):
        if self.shared["preys"].value > 1 :
            self.energy -= 20
            new_prey_proc = mp.Process(target=run_prey, args=(self.shared, self.lock))
            new_prey_proc.start()
            self.shared["preys"].value += 1
            print(f"Une nouvelle proie est née.")

    def live_one_cycle(self):
        with self.lock:
            if self.pid not in self.shared["prey_states"]:
                self.alive = False
                return 

        # Déplacement et alimentation
            self.deplacement_proie()

            # Métabolisme
            self.energy -= 1
            self.update_state()

            # Reproduction
            if self.energy > R:
                self.reproduce()

            # Mort
            if self.energy <= 0:
                self.die("de faim")

def run_prey(shared, lock):
    pid = os.getpid()
    prey = Prey(shared, lock)
    
    msg = f"iam_prey:{pid}:{prey.x}:{prey.y}"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 6666))
        s.sendall(msg.encode())
        s.close()
    except Exception as e:
        print(f"Erreur connexion socket: {e}")
        return

    while prey.alive:
        prey.live_one_cycle()
        time.sleep(0.15)