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
        time.sleep(1)

        with lock:
            if random.random() < 0.1:
                shared_data["drought"].value = not shared_data["drought"].value

            if not shared_data["drought"].value and shared_data["grass"].value<grass_lim:
                shared_data["grass"].value += 2
            else:
                shared_data["grass"].value += 0

            stats = {
                    "grass": shared_data["grass"].value,
                    "preys": shared_data["preys"].value,
                    "predators": shared_data["predators"].value,
                    "drought": shared_data["drought"].value
                }
            
            # 3. ENVOI DANS LA QUEUE (en dehors du lock pour ne pas bloquer)
        queue.put(stats)

        

def socket_server(shared_data, lock):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 6666))
    server.listen()
    
    while True:
        client_sock, addr = server.accept() 
        msg = client_sock.recv(1024).decode()

        if msg == "new_prey":
            # On crée le processus ICI. 
            # Comme c'est un enfant de env, il RECOIT le lock et le shared_data
            p = mp.Process(target=run_prey, args=(shared_data, lock))
            p.start()
            with lock:
                shared_data["preys"].value += 1
            print(f"Nouvelle proie créée par le socket !")

        elif msg == "new_predator":
            # On crée le processus ICI. 
            # Comme c'est un enfant de env, il RECOIT le lock et le shared_data
            p = mp.Process(target=run_predator, args=(shared_data, lock))
            p.start()
            with lock:
                shared_data["predators"].value += 1
            print(f"Nouveau predator créée par le socket !")
            
        client_sock.close()


# MAIN 
if __name__ == "__main__":
    mp.set_start_method("spawn")
    
    manager = mp.Manager()
    queue = mp.Queue() # La file de messages
    lock = mp.Lock()
    
    shared_data = {
        "grass": mp.Value("i", 50),
        "preys": mp.Value("i", 0),
        "prey_states": manager.dict(),
        "predators": mp.Value("i", 0),
        "drought": mp.Value("b", False),
    }

    # Lancement des deux processus piliers
    env_p = mp.Process(target=env, args=(shared_data, lock, queue))
    disp_p = mp.Process(target=run_display, args=(queue,))
    
    env_p.start()
    disp_p.start()
    
    env_p.join()
    disp_p.join()
