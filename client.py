import socket
import sys

def add_animal(animal_type):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 6666))
    if animal_type == "prey":
        s.sendall(b"new_prey")
    else:
        s.sendall(b"new_predator")
    s.close()

# Utilisation : python client.py prey  OU  python client.py predator
if __name__ == "__main__":
    if len(sys.argv) > 1:
        add_animal(sys.argv[1])
    