from display import run_display
import time
import multiprocessing as mp
import random
import socket
import threading
from prey import run_prey 
from predator import run_predator

HOST = "localhost"
PORT = 6666

def env(shared_data, lock, queue):
    grass_lim = 100
    t = threading.Thread(target=socket_server, args=(shared_data, lock), daemon=True)
    t.start()
    
    while True:
        time.sleep(0.5)
        
        with lock:
            states = shared_data["grass_states"]
            positions = shared_data["static_grass_pos"]

            visible_grass = [positions[i] for i, alive in enumerate(states) if alive]

            stats = {
                "grass": len(visible_grass),
                "grass_coords": visible_grass,
                "preys": shared_data["preys"].value,
                "predators": shared_data["predators"].value,
                "drought": shared_data["drought"].value,
                "preys_coords": list(shared_data["prey_positions"].values()),
                "preds_coords": list(shared_data["pred_positions"].values())
            }
        queue.put(stats)

def socket_server(shared_data, lock):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    
    while True:
        client_sock, _ = server.accept() 
        try:
            msg = client_sock.recv(1024).decode()
            if msg == "new_prey":
                p = mp.Process(target=run_prey, args=(shared_data, lock))
                p.start()
                with lock:
                    shared_data["preys"].value += 1
            elif msg == "new_predator":
                p = mp.Process(target=run_predator, args=(shared_data, lock))
                p.start()
                with lock:
                    shared_data["predators"].value += 1
            elif msg == "drought_on":
                shared_data["drought"].value = not shared_data["drought"].value
        finally:
            client_sock.close()

# MAIN 
if __name__ == "__main__":
    mp.set_start_method("spawn")
    
    manager = mp.Manager()
    queue = mp.Queue()
    lock = mp.Lock()
    
    grass_coords = [(random.uniform(5, 95), random.uniform(5, 95)) for _ in range(400)]
    grass_states = manager.list([True] * 100)
    
    shared_data = {
        "grass": mp.Value("i", 20),
        "preys": mp.Value("i", 0),
        "predators": mp.Value("i", 0),
        "drought": mp.Value("b", False),
        "prey_states": manager.dict(), 
        "prey_positions": manager.dict(), 
        "pred_positions": manager.dict(),  
        "locked_preys": manager.dict(),
        "locked_grass": manager.dict(), 
        "static_grass_pos": grass_coords,
        "grass_states" : grass_states
    }

    env_p = mp.Process(target=env, args=(shared_data, lock, queue))
    disp_p = mp.Process(target=run_display, args=(queue,))
    
    env_p.start()
    disp_p.start()
    
    env_p.join()
    disp_p.join()