import time
import multiprocessing as mp
import random


def env(shared, lock):
    """
    Environment process.
    Manages global state of the ecosystem.
    """
    grass_lim = 100
    while True:
        time.sleep(1)
        lock.acquire()

        #climate
        if random.random() < 0.1:
            shared["drought"].value = not shared["drought"].value

        #grass growth
        if not shared["drought"].value and shared["grass"].value<grass_lim:
            shared["grass"].value += 2
        else:
            shared["grass"].value += 0

        print(
            f"Grass: {shared['grass'].value} | "
            f"Preys: {shared['preys'].value} | "
            f"Predators: {shared['predators'].value} | "
            f"Drought: {shared['drought'].value}"
        )

        lock.release()

def inc_shared_prey(shared, lock):
    with lock:
        shared["preys"].value += 1

def inc_shared_predator(shared, lock):
    with lock:
        shared["predators"].value += 1


if __name__ == "__main__":
    mp.set_start_method("spawn") #creates child process from scratch, to avoid bugs with the shared data
    #shared memory
    shared = {
        "grass": mp.Value("i", 50),
        "preys": mp.Value("i", 0),
        "predators": mp.Value("i", 0),
        "drought": mp.Value("b", False),
    }

    lock = mp.Lock()
    env_process = mp.Process(target=env, args=(shared, lock))
    env_process.start()
    env_process.join()
