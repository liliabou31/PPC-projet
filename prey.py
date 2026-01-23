import multiprocessing as mp
import time
import socket
import random
import os
import math  # <--- Crucial pour math.sqrt

# Seuils 
H = 30  
R = 80  
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
        self.x = random.uniform(0, 100)
        self.y = random.uniform(0, 100)
        self.vision_radius = 50
        self.target_grass_index = None        
        with self.lock:
            self.shared["prey_states"][self.pid] = self.state
            self.shared["prey_positions"][self.pid] = (self.x, self.y)

    def find_nearest_grass(self):
        with self.lock:
            grass_positions = self.shared["static_grass_pos"]
            occupied_grass = self.shared["locked_grass"] 
            
            best_index = None
            max_dist = float("inf")
            
            for i in range(self.shared["grass"].value):
                if i not in occupied_grass and self.shared["grass_states"][i] == True: 
                    pos = grass_positions[i]
                    #dist = abs(self.x - pos[0])+ abs(self.y - pos[1])
                    dist = math.sqrt((self.x - pos[0])**2 + (self.y - pos[1])**2)
                    if dist < max_dist:
                        max_dist = dist
                        best_index = i
            
            if best_index is not None:
                self.shared["locked_grass"][best_index] = self.pid
                self.target_grass_index = best_index

    def move(self):
        has_moved_to_target = False
        if self.target_grass_index is not None:
            with self.lock:
                if self.target_grass_index >= self.shared["grass"].value:
                    self.target_grass_index = None
                else:
                    target_pos = self.shared["static_grass_pos"][self.target_grass_index]
            
            # Si la proie a repéré de l'herbe

            if self.target_grass_index is not None:
                dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
                dist = math.sqrt(dx**2 + dy**2)
                
                if dist > 1.0:
                    step = min(2.5, dist)
                    self.x += (dx / dist) * step
                    self.y += (dy / dist) * step
                    has_moved_to_target = True
                    # 2. On recalcule la distance IMMEDIATEMENT après le mouvement
                    new_dx = target_pos[0] - self.x
                    new_dy = target_pos[1] - self.y
                    new_dist = math.sqrt(new_dx**2 + new_dy**2)

                    # 3. Si on est dessus, on mange tout de suite !
                    if new_dist < 1.5: 
                        self.eat()
                #else:
                #   self.eat()
        
        # Errance 

        if not has_moved_to_target:
            self.x += random.uniform(-2, 2)
            self.y += random.uniform(-2, 2)
            if self.state == "active": # Si la proie a faim
                self.find_nearest_grass()
        # Sécurité pour que la proie ne sort pas de la map
        self.x = max(0, min(100, self.x))
        self.y = max(0, min(100, self.y))
        
        with self.lock:
            if self.pid in self.shared["prey_positions"]:
                self.shared["prey_positions"][self.pid] = (self.x, self.y)

    def eat(self):
        with self.lock:
            idx = self.target_grass_index
            if idx is not None and idx < len(self.shared["grass_states"]):
                self.shared["grass_states"][idx] = False # l'herbe n'est pas supprimée mais rendue invisible
                self.energy += 20
                
                if idx in self.shared["locked_grass"]:
                    del self.shared["locked_grass"][idx] # Suppression de l'herbe
            self.target_grass_index = None

    def update_state(self):
        old_state = self.state
        if self.energy < H:
            self.state = "active"
        elif self.energy > H + 15:
            self.state = "passive"
        
        if old_state != self.state:
            with self.lock:
                self.shared["prey_states"][self.pid] = self.state

    def die(self, reason):
        self.alive = False
        with self.lock:
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
        if len(self.shared["prey_states"]) >= 2 :
            self.energy -= 40 
            new_prey_proc = mp.Process(target=run_prey, args=(self.shared, self.lock))
            new_prey_proc.start()
            with self.lock:
                self.shared["preys"].value += 1
            print(f"Une nouvelle proie est née.")

    def live_one_cycle(self):
        with self.lock:
            if self.pid not in self.shared["prey_states"]:
                self.alive = False
                return 

        # Déplacement et alimentation
        self.move()

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
    prey = Prey(shared, lock)
    while prey.alive:
        prey.live_one_cycle()
        time.sleep(0.15)