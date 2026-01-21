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

    # --- LANCER LE SERVEUR ---
    try:
        t = threading.Thread(target=socket_server, args=(shared_data, lock), daemon=True)
        t.start()
        print("[DEBUG] Thread socket lancé avec succès")
    except Exception as e:
        print(f"[DEBUG] Erreur lors du lancement du thread : {e}")
    grass_lim = 100
    # ... setup socket et signal ici ...

    while True:
        time.sleep(0.1) # 20 images par seconde pour la fluidité

        with lock:
            # 1. Extraction propre des positions (Proies)
            prey_positions = []
            for pid, data in shared_data["prey_states"].items():
                # On vérifie si c'est bien le format ((x, y), "etat")
                if isinstance(data, (list, tuple)) and len(data) > 0:
                    prey_positions.append(data[0]) 

            # 2. Extraction propre des positions (Prédateurs)
            pred_positions = []
            # .get() évite que le code crash si le dictionnaire n'existe pas encore
            for pid, data in shared_data.get("predator_states", {}).items():
                if isinstance(data, (list, tuple)) and len(data) > 0:
                    pred_positions.append(data[0])

            # 3. Gestion de l'herbe
            if not shared_data["drought"].value and shared_data["grass"].value < grass_lim:
                shared_data["grass"].value += 1

            # 4. Préparation du paquet pour Pygame
            stats = {
                "grass": shared_data["grass"].value,
                "preys_coords": prey_positions, 
                "preds_coords": pred_positions,
                "drought": shared_data["drought"].value
            }
        
        # 5. Envoi à la queue (hors du lock pour la performance)
        queue.put(stats)
        

def socket_server(shared_data, lock):
    print("[DEBUG] Entrée dans socket_server") # <-- Ajoute ça
    try : 
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 6666))        
        server.listen(5)
        print("[DEBUG] Serveur en écoute sur 127.0.0.1:6666") # <-- Ajoute ça
        
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
        
    except Exception as e:
            print(f"[ERROR SOCKET] {e}")


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
