import multiprocessing as mp
import time
import socket
import math
import os
import random

# Seuils 
H = 40  
R = 80  
HOST = "localhost"
PORT = 6666

class Predator:
    def __init__(self, shared_data, lock):
        self.energy = 60
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
        if prey_pid in self.shared["prey_states"]:
            del self.shared["prey_states"][prey_pid]
            if prey_pid in self.shared["prey_positions"]:
                del self.shared["prey_positions"][prey_pid]
            
            if self.shared["preys"].value > 0:
                self.shared["preys"].value -= 1
            
            self.energy += 45
            print(f"[PREDATEUR {self.pid}] a dévoré la proie {prey_pid}")
        
        if prey_pid in self.shared["locked_preys"]:
            del self.shared["locked_preys"][prey_pid]
        self.target_prey_pid = None

    def die(self):
        self.alive = False
        if self.pid in self.shared["pred_positions"]:
            del self.shared["pred_positions"][self.pid]
        if self.target_prey_pid in self.shared["locked_preys"]:
            del self.shared["locked_preys"][self.target_prey_pid]
        if self.shared["predators"].value > 0:
            self.shared["predators"].value -= 1
        print(f"[PREDATEUR {self.pid}] est mort de faim.")

    def reproduce(self):
        if self.shared["predators"].value >= 2 :
            self.energy -= 35
            p = mp.Process(target=run_predator, args=(self.shared, self.lock))
            p.start()
            self.shared["predators"].value += 1
    
    def live_one_cycle(self):
        self.energy -= 1
        self.update_state()
        with self.lock:
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
            self.shared["pred_positions"][self.pid] = (self.x, self.y)

            if self.energy > R:
                self.reproduce()

            if self.energy <= 0:
                self.die()

def run_predator(shared, lock):
    pid = os.getpid()
    pred = Predator(shared, lock)
    
    # 1. Se signaler à l'ENV via Socket
    msg = f"iam_predator:{pid}:{pred.x}:{pred.y}"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 6666))
        s.sendall(msg.encode())
        s.close()
    except Exception as e:
        print(f"Erreur connexion socket: {e}")
        return
    
    while pred.alive:
        pred.live_one_cycle()
        time.sleep(0.15)
