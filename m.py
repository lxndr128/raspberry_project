import socket
import json
import threading
from time import sleep


dump = []


def listen(port: int):
    global dump
    sock = socket.socket()
    sock.bind(("", port))

    while True:
        sock.listen(1)
        conn, addr = sock.accept()
        data = conn.recv(4096)

        get = json.loads(data)
        if get not in dump:
            dump.append(get)


def send_message(addr: tuple, message):
    sock = socket.socket()
    sock.connect(addr)
    mess = json.dumps(message)
    sock.send(bytes(mess, encoding='utf-8'))
    sock.close()


if __name__ == "__main__":
    x = threading.Thread(target=listen, args=(9003,))
    x.start()

    d = []
    while True:
        if d != dump:
            print(dump)
            d = dump.copy()
        sleep(0.2)
