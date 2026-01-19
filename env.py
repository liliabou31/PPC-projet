from IPython.display import run_display
import time
import multiprocessing as mp
import random
import socket
import threading


HOST = "localhost"
PORT = 6666

def env(shared_data, lock):

    grass_lim = 100
    t = threading.Thread(target=socket_server, args=(shared_data, lock), daemon=True)
    t.start()
    while True:
        time.sleep(1)
        lock.acquire()

        if random.random() < 0.1:
            shared_data["drought"].value = not shared_data["drought"].value

        if not shared_data["drought"].value and shared_data["grass"].value<grass_lim:
            shared_data["grass"].value += 2
        else:
            shared_data["grass"].value += 0

        print(
            f"Grass: {shared_data['grass'].value} | "
            f"Preys: {shared_data['preys'].value} | "
            f"Predators: {shared_data['predators'].value} | "
            f"Drought: {shared_data['drought'].value}"
        )

        lock.release()

def inc_shared_data_data_prey(shared_data, lock):
    with lock:
        shared_data["preys"].value += 1

def inc_shared_data_data_predator(shared_data, lock):
    with lock:
        shared_data["predators"].value += 1

def socket_server(shared_data, lock):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 6666))
    server.listen()
    
    while True:
        client_sock, addr = server.accept() 
        print(f"[ENV] Connexion acceptée de {addr}")
        msg = client_sock.recv(1024).decode()

        if msg == "new_prey":
            with lock:
                shared_data["preys"].value += 1
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
