import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import socket
import random

def send_cmd(msg):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect(("localhost", 6666))
            s.sendall(msg.encode())
    except:
        pass

def run_display(queue, command_queue):
    plt.ion()
    fig, ax = plt.subplots(figsize=(9, 7))
    plt.subplots_adjust(bottom=0.2)
    
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    
    # 1. HERBE : On garde des positions fixes car l'herbe ne bouge pas
    grass_pos = [(random.uniform(5, 95), random.uniform(5, 95)) for _ in range(200)]

    # 2. OBJETS GRAPHIQUES
    grass_plot, = ax.plot([], [], 'go', markersize=4, label="Herbe (Vert)")
    # Les proies et prédateurs n'ont plus de positions pré-calculées
    prey_plot,  = ax.plot([], [], 'bs', markersize=6, label="Proie (Bleu)")
    pred_plot,  = ax.plot([], [], 'r^', markersize=8, label="Predateur (Rouge)")

    ax_prey = plt.axes([0.05, 0.05, 0.25, 0.06])
    ax_pred = plt.axes([0.37, 0.05, 0.25, 0.06])
    ax_drought = plt.axes([0.70, 0.05, 0.25, 0.06])

    btn_prey = Button(ax_prey, ' + Proie ', color='deepskyblue', hovercolor="#B7EFFF")
    btn_pred = Button(ax_pred, ' + Prédateur ', color='tomato', hovercolor="#FEA872")
    btn_drought = Button(ax_drought, ' Sécheresse ', color='gold', hovercolor="#FFF49F")

    btn_prey.on_clicked(lambda e: command_queue.put("new_prey"))
    btn_prey.on_clicked(lambda e: command_queue.put("new_predator"))
    btn_prey.on_clicked(lambda e: command_queue.put("drought_on"))

    while True:
        stats = queue.get()
        if stats == "STOP": break

        if isinstance(stats, dict):
            # On récupère la liste des coordonnées VIVANTES envoyée par env
            g_coords = stats.get("grass_coords", []) 
            
            if g_coords:
                # On "dézippe" la liste de tuples [(x1,y1), (x2,y2)] en deux listes [x], [y]
                xg, yg = zip(*g_coords)
                grass_plot.set_data(xg, yg)
            else:
                # Si la liste est vide (plus d'herbe), on vide le plot
                grass_plot.set_data([], [])

            # --- MISE À JOUR PROIES (MOUVEMENT RÉEL) ---
            p_coords = stats.get("preys_coords", [])
            if p_coords:
                xp, yp = zip(*p_coords)
                prey_plot.set_data(xp, yp)
            else:
                prey_plot.set_data([], [])

            # --- MISE À JOUR PREDATEURS (MOUVEMENT RÉEL) ---
            pr_coords = stats.get("preds_coords", [])
            if pr_coords:
                xr, yr = zip(*pr_coords)
                pred_plot.set_data(xr, yr)
            else:
                pred_plot.set_data([], [])

            # --- INTERFACE ---
            ax.set_facecolor("#FFFAD4" if stats.get('drought') else 'white')
            ax.set_title(f"Simulation PPC | H: {stats['grass']} | P: {stats['preys']} | L: {stats['predators']}")

        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.1)

    plt.close()