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
    t = threading.Thread(target=socket_server, args=(shared_data, lock), daemon=True)
    t.start()
    
    while True:
        time.sleep(0.5)
        
        with lock:
            # 1. On récupère TOUJOURS la version la plus à jour (celle modifiée par les proies)
            current_pos = shared_data["static_grass_pos"]
            current_states = shared_data["grass_states"]
            modified = False
            dead = current_states.count(False)
            alive = current_states.count(True)
            #print(f"[ENV] grass alive={alive} dead={dead}")
            is_drought = shared_data["drought"].is_set()

            if not is_drought:
                if len(current_pos) < 400:
                    for _ in range(3):
                        new_coord = (random.uniform(5, 95), random.uniform(5, 95))
                        current_pos.append(new_coord)
                        current_states.append(True)
                        modified = True
            else:
                if current_states and random.random() < 0.5:
                    i = random.randint(0, len(current_states) - 1)
                    current_states[i] = False
                    modified = True

            # 2. On ne réassigne QUE si env a ajouté ou supprimé de l'herbe
            # Sinon, on laisse les modifs des proies tranquilles
            if modified:
                shared_data["static_grass_pos"] = current_pos
                shared_data["grass_states"] = current_states
        
            alive_grass = [pos for pos, state in zip(current_pos, current_states) if state]

            stats = {
                "grass": len(alive_grass),
                "grass_coords": alive_grass,
                "preys": shared_data["preys"].value,
                "predators": shared_data["predators"].value,
                "drought": is_drought,
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
                with lock: shared_data["preys"].value += 1
            elif msg == "new_predator":
                p = mp.Process(target=run_predator, args=(shared_data, lock))
                p.start()
                with lock: shared_data["predators"].value += 1
            elif msg == "drought_on":
                if shared_data["drought"].is_set():
                    shared_data["drought"].clear()
                    print("[SIGNAL] Fin de la sécheresse")
                else:
                    shared_data["drought"].set()
                    print("[SIGNAL] Début de la sécheresse")
        finally:
            client_sock.close()

# MAIN 
if __name__ == "__main__":
    mp.set_start_method("spawn")
    
    manager = mp.Manager()
    queue = mp.Queue()
    lock = mp.Lock()

    nb_grass = 200
    grass_coords = manager.list([(random.uniform(5, 95), random.uniform(5, 95)) for _ in range(nb_grass)])
    grass_states = manager.list([True] * nb_grass)
    
    drought_event = mp.Event() 
    
    shared_data = {
        "grass": mp.Value("i", nb_grass),
        "locked_grass": manager.dict(), 
        "static_grass_pos": grass_coords,
        "grass_states" : grass_states,

        "preys": mp.Value("i", 0),
        "prey_states": manager.dict(), 
        "prey_positions": manager.dict(), 
        "locked_preys": manager.dict(),

        "predators": mp.Value("i", 0),
        "pred_positions": manager.dict(),

        "drought": drought_event
    }

    env_p = mp.Process(target=env, args=(shared_data, lock, queue))
    disp_p = mp.Process(target=run_display, args=(queue,))
    
    env_p.start()
    disp_p.start()
    
    env_p.join()
    disp_p.join()