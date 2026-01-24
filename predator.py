import multiprocessing as mp
import time
import socket
import math
import os
import random

# Seuils 
H = 30  
R = 80  
HOST = "localhost"
PORT = 6666

class Predator:
    def __init__(self, shared_data, lock):
        self.energy = 50
        self.state = "passive"
        self.shared = shared_data
        self.lock = lock
        self.alive = True
        self.pid = os.getpid()
        self.x = random.uniform(0, 100)
        self.y = random.uniform(0, 100)
        self.target_prey_pid = None
        self.vision_radius = 100

        with self.lock:
            self.shared["pred_positions"][self.pid] = (self.x, self.y)

    def update_state(self):
        if self.energy < H:
            self.state = "active"
        elif self.energy > H + 20:
            self.state = "passive"

    def find_closest_prey(self):
        with self.lock:
            preys_pos = dict(self.shared["prey_positions"])
            locks = self.shared["locked_preys"]
            
            best_pid = None
            min_dist = self.vision_radius

            for pid, pos in preys_pos.items():
                if pid not in locks:
                    dist = math.sqrt((self.x - pos[0])**2 + (self.y - pos[1])**2)
                    if dist < min_dist:
                        min_dist = dist
                        best_pid = pid
            
            if best_pid:
                self.shared["locked_preys"][best_pid] = self.pid
                self.target_prey_pid = best_pid

    def move_towards_target(self):
        """ Se déplace vers la proie verrouillée """
        with self.lock:
            if self.target_prey_pid not in self.shared["prey_positions"]:
                self.target_prey_pid = None
                return

            target_pos = self.shared["prey_positions"][self.target_prey_pid]
        
        dx = target_pos[0] - self.x
        dy = target_pos[1] - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 1.5:
            self.x += (dx / dist) * 2.5
            self.y += (dy / dist) * 2.5
        else:
            self.eat_prey(self.target_prey_pid)

    def eat_prey(self, prey_pid):
        """ Supprime la proie et gagne de l'énergie """
        with self.lock:
            if prey_pid in self.shared["prey_states"]:
                del self.shared["prey_states"][prey_pid]
                if prey_pid in self.shared["prey_positions"]:
                    del self.shared["prey_positions"][prey_pid]
                
                if self.shared["preys"].value > 0:
                    self.shared["preys"].value -= 1
                
                self.energy += 40
                print(f"[PREDATEUR {self.pid}] a dévoré la proie {prey_pid}")
            
            if prey_pid in self.shared["locked_preys"]:
                del self.shared["locked_preys"][prey_pid]
            self.target_prey_pid = None

    def die(self):
        self.alive = False
        with self.lock:
            if self.pid in self.shared["pred_positions"]:
                del self.shared["pred_positions"][self.pid]
            if self.target_prey_pid in self.shared["locked_preys"]:
                del self.shared["locked_preys"][self.target_prey_pid]
            if self.shared["predators"].value > 0:
                self.shared["predators"].value -= 1
        print(f"[PREDATEUR {self.pid}] est mort de faim.")

    def reproduce(self):
        if len(self.shared["predators"].value) >= 2 :
            self.energy -= 35
            p = mp.Process(target=run_predator, args=(self.shared, self.lock))
            p.start()
            with self.lock:
                self.shared["predators"].value += 1
    
    def live_one_cycle(self):
        self.energy -= 1
        self.update_state()

        if self.state == "active":
            if self.target_prey_pid is None:
                self.find_closest_prey()
            
            if self.target_prey_pid:
                self.move_towards_target()
            else:
                self.x += random.uniform(-2, 2)
                self.y += random.uniform(-2, 2)
        else:
            self.x += random.uniform(-1, 1)
            self.y += random.uniform(-1, 1)

        self.x = max(0, min(100, self.x))
        self.y = max(0, min(100, self.y))
        with self.lock:
            self.shared["pred_positions"][self.pid] = (self.x, self.y)

        if self.energy > R:
            self.reproduce()

        if self.energy <= 0:
            self.die()

def run_predator(shared, lock):
    predator = Predator(shared, lock)
    while predator.alive:
        predator.live_one_cycle()
        time.sleep(0.1)