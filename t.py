from datetime import datetime as dt, timedelta
import socket
import json


def send_message(addr: tuple, message):
    sock = socket.socket()
    sock.connect(addr)
    mess = json.dumps(message)
    sock.send(bytes(mess, encoding='utf-8'))
    sock.close()


data = [{"NAME": "Иванов Иван Иванович", "BIRTHDAY": "20.12.90",
        "ID": "12345678", "DATE": "2022-01-20",
         "TIME": [{"hours": 11, "minutes": 30}, {"hours": 21, "minutes": 00}],
         "BARCODE": "123456", }]

send_message(("", 9003), data)
