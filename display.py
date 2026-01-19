import time

def run_display(queue):
    print("--- Démarrage de l'affichage ---")
    while True:
        if not queue.empty():
            stats = queue.get()
            # On nettoie un peu la console (optionnel)
            print("\033[H\033[J", end="") 
            print("========= ÉCOSYSTÈME =========")
            print(f" Herbe      : {stats['grass']}")
            print(f" Proies     : {stats['preys']}")
            print(f" Prédateurs : {stats['predators']}")
            print(f" Sécheresse : {'OUI' if stats['drought'] else 'NON'}")
            print("==============================")
        time.sleep(0.5)