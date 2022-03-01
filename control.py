from datetime import datetime as dt, timedelta
import socket
import sys
import pickle


IP = "192.168.3.27"
PORT = 9003


def send_message(addr: tuple, message):
    sock = socket.socket()
    sock.connect(addr)
    mess = pickle.dumps(message)
    sock.send(mess)
    sock.close()

date = str(dt.today()).split()[0]

def command(arg):
    if arg == "1":
        data = [{"NAME": "Иванов Иван Иванович", "BIRTHDAY": "20.12.90",
                 "ID": "12345678", "DATE": date,
                 "TIME": [timedelta(hours=0, minutes=0), timedelta(hours=23, minutes=59)],
                 "BARCODE": "123456", },
                 {"NAME": "Дмитриев Дмитрий Дмитриевич", "BIRTHDAY": "09.11.88",
                  "ID": "12345679", "DATE": date,
                  "TIME": [timedelta(hours=0, minutes=0), timedelta(hours=23, minutes=59)],
                  "BARCODE": "65833254", }]
        send_message((IP, PORT), data)
    elif arg == "2":
        data = [{"COMMAND": "shutdown"}]
        send_message((IP, PORT), data)
    elif arg == "3":
        data = [{"COMMAND": "reboot"}]
        send_message((IP, PORT), data)
    elif arg == "4":
        data = [{"COMMAND": "free-mode-on"}]
        send_message((IP, PORT), data)
    elif arg == "5":
        data = [{"COMMAND": "free-mode-off"}]
        send_message((IP, PORT), data)
    elif arg == "6":
        data = [{"COMMAND": "reboot with backup"}]
        send_message((IP, PORT), data)
    else:
        print("Ошибка")

arg = sys.argv

if len(arg) == 1:
    print("1 - Отправить данные")
    print("2 - Выключить панель")
    print("3 - Перезагрузить панель")
    print("4 - Включить реле")
    print("5 - Выключить реле")
    print("6 - Перезагрузить панель сохранив данные")
    command(input("\nВведите номер команды: "))
else:
    command(arg[1])
