from datetime import datetime as dt, timedelta
from PyQt5 import QtCore, QtGui, QtWidgets
from scan import b_read
import RPi.GPIO as GPIO
import socket
import pickle
import time
import threading
import sys
import os
import functools
from pyautogui import size


ROOM_ID = "00001"

SERVER_IP = ""
SERVER_PORT = ""

IP = "192.168.3.27"
PORT = 9003

FREE_MODE = 0
USING_TIME = 1.5
BARCODE = ""
BARCODE_READER_ERROR = 0
LISTEN_PORT_ERROR = 0
DATA = []
BUSY = 0
USER_NUMBER = 0


def backup_file(a):
    global DATA

    if a == "make":
        with open("/home/pi/GUI/backup", "wb") as b:
            b.write(pickle.dumps(DATA))
    elif a == "load":
        if os.path.isfile("/home/pi/GUI/backup"):
            with open("/home/pi/GUI/backup", "rb") as b:
                DATA = pickle.loads(b.read())
    elif a == "delete":
        if os.path.isfile("/home/pi/GUI/backup"):
            os.remove("/home/pi/GUI/backup")


def write_log(event):
    if event == "start" or event == "stop":
        data = DATA[USER_NUMBER]["ID"] + \
            "_" + event + "_" + ROOM_ID + "_" + str(dt.today())
    else:
        data = event + "_" + ROOM_ID + "_" + str(dt.today())
    with open("/home/pi/GUI/logs.txt", "a") as log:
        log.write(data+"\n")


def relay(switch):
    if switch:
        sw = GPIO.HIGH
    else:
        sw = GPIO.LOW
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(21, GPIO.OUT)
    GPIO.output(21, sw)


def execute_the_command(command):
    write_log(command)

    if command == "shutdown":
        backup_file("delete")
        os.system('shutdown -h now')

    elif command == "reboot with backup":
        os.system('reboot')

    elif command == "reboot":
        backup_file("delete")
        os.system('reboot')

    elif command == "free-mode-on":
        if not BUSY:
            switch_bbr(1, True)

    elif command == "free-mode-off":
        if FREE_MODE:
            switch_bbr(0, True)


def check_barcode():
    global DATA
    global USER_NUMBER

    if DATA == [] or BARCODE == "":
        return False

    for i in range(len(DATA)):
        if DATA[i]["BARCODE"] == BARCODE:
            USER_NUMBER = i
            break
        elif i < len(DATA):
            continue
        return False

    date = str(dt.today()).split()
    date[1] = date[1].split(":")
    time = timedelta(hours=int(date[1][0]), minutes=int(date[1][1]))

    a = date[0] == DATA[USER_NUMBER]["DATE"]
    b = DATA[USER_NUMBER]["TIME"][0] <= time < DATA[USER_NUMBER]["TIME"][1]

    if a and b:
        if "USING" not in DATA[USER_NUMBER].keys():
            DATA[USER_NUMBER]["USING"] = timedelta(minutes=USING_TIME)
            return True
        elif DATA[USER_NUMBER]["USING"] != "STOP":
            return True
    else:
        DATA[USER_NUMBER]["USING"] = "STOP"

    return False


def listen_port():

    def sub_listen():
        global DATA
        try:
            sock = socket.socket()
            sock.bind((IP, PORT))
        except Exception as e:
            print("Ошибка сети\n", e)
            write_log(str(e))
            if FREE_MODE:
                relay(0)
            sys.exit()

        counter = 0

        while True:
            try:
                sock.listen(1)
                conn, addr = sock.accept()
                data = conn.recv(4096)
                counter = 0
            except Exception as e:
                counter += 1
                write_log(str(e))
                sleep(3)

                if counter > 1:
                    global LISTEN_PORT_ERROR
                    LISTEN_PORT_ERROR = 1
                    break
                else:
                    continue

            get = pickle.loads(data)

            if "COMMAND" in get[0].keys():
                execute_the_command(get[0]["COMMAND"])
            else:
                for i in DATA:
                    flag = 0
                    for j in get:
                        if i["ID"] == j["ID"]:
                            flag = 1
                            break
                    if not flag:
                        DATA.append(j)

                if DATA == []:
                    DATA.extend(get)

    listen = threading.Thread(target=sub_listen, args=())
    listen.daemon = True
    listen.start()


def read_barcode():

    def sub_read():
        global BARCODE
        counter = 0
        while True:
            if not BUSY and DATA != []:
                try:
                    data = b_read()
                    BARCODE = "".join([i for i in data if i.isdigit()])
                    counter = 0
                except Exception as e:
                    write_log(str(e))
                    counter += 1
                    if counter > 1:
                        BARCODE_READER_ERROR = 1
                        counter = 0
                        break
                    os.system("uhubctl -l 1-1 -a 0")
                    time.sleep(5)
                    os.system("uhubctl -l 1-1 -a 1")
                    time.sleep(5)

    reader = threading.Thread(target=sub_read)
    reader.daemon = True
    reader.start()


def switch_bbr(a, b=None):
    global FREE_MODE
    global BARCODE
    global BUSY

    BARCODE = ""
    BUSY = a
    relay(a)

    if b == True:
        FREE_MODE = a


class Window(QtWidgets.QWidget):
    global BARCODE

    def __init__(self):
        super().__init__()
        relay(0)
        backup_file("load")

        self.setCursor(QtCore.Qt.BlankCursor)
        self.background_picture = QtWidgets.QLabel(self)
        self.background_picture.setGeometry(0, 0, 480, 320)
        self.background_picture.setStyleSheet("background-image: url(/home/pi/GUI/background.png);")
        self.background_picture.show()

        listen_port()
        read_barcode()

        self.set_timer()
        self.set_stop_button()
        self.set_name_label()
        self.set_start_label()

        self.showFullScreen()

    def set_stop_button(self):
        self.mode = 0
        self.button = QtWidgets.QPushButton('Стоп', self)
        self.button.setGeometry(155, 200, 170, 85)
        self.button.setFont(QtGui.QFont('Times New Roman', 30))
        self.button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.button.clicked.connect(self.stop_work)
        self.button.setStyleSheet('QPushButton {border-radius: \
                                    40px 40px 40px 40px; border:\
                                     15px #c284c0; background-color:\
                                      #c284c0;  color: #383838;}')
        self.button.hide()

    def change_stop_button(self):

        colors = ["#84c286", "#c28484", "#c284c0"]

        stl = f'QPushButton {{border-radius: \
                40px 40px 40px 40px; border:\
                    15px {colors[self.mode]}; background-color:\
                        {colors[self.mode]};  color: #383838;}}'

        self.button.setStyleSheet(stl)

        if self.mode == 2:
            self.mode = 0
        else:
            self.mode += 1

    def set_timer(self):
        self.s = size()
        self.check_free_mode = 0
        self.label = QtWidgets.QLabel(self)
        self.label.setStyleSheet("color: #383838;")
        self.label.setFont(QtGui.QFont('Arial', 90))

        if USING_TIME > 60:
            self.x = 0
            self.label.move(40, 60)
        else:
            self.x = 2
            self.label.move(92, 60)

        self.label.setText(str(timedelta(minutes=USING_TIME))[self.x:])
        self.label.adjustSize()
        self.label.hide()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.start_timer)
        self.timer.start()

    def set_name_label(self):
        self.nlabel = QtWidgets.QLabel(self)
        self.nlabel.move(20, 12)
        self.nlabel.setStyleSheet("color: #1a1a1a;")
        self.nlabel.setFont(QtGui.QFont('Times New Roman', 15))

    def set_start_label(self):
        self.slabel = QtWidgets.QLabel(self)
        self.slabel.setStyleSheet("letter-spacing: 3px; color: #383838;")
        self.slabel.move(18, 123)
        self.slabel.setFont(QtGui.QFont('Impact', 26))
        self.slabel.setText("Отсканируйте штрих-код")
        self.slabel.adjustSize()
        self.slabel.show()

    def switch_start_label(self, mode: int):
        flag = 1

        if mode == 1:
            move = [115,120]
            text = "Время вышло!"
        elif mode == 0:
            move = [18,123]
            text = "Отсканируйте штрих-код"
        elif mode == 2:
            move = [70,123]
            text = "Cвободный режим"
        else:
            flag = 0

        if flag:
            self.slabel.move(*move)
            self.slabel.setText(text)
            self.slabel.adjustSize()
            self.slabel.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            if FREE_MODE or BUSY:
                relay(0)
            sys.exit()

    def plus_one_second(self):
        if DATA[USER_NUMBER]["USING"] == timedelta(seconds=0):
            DATA[USER_NUMBER]["USING"] = "STOP"
            self.stop_work()
        elif DATA[USER_NUMBER]["USING"] != "STOP":
            if self.barcode == BARCODE:
                DATA[USER_NUMBER]["USING"] -= timedelta(seconds=1)
                self.stop_work()
            else:
                DATA[USER_NUMBER]["USING"] -= timedelta(seconds=1)
                self.label.setText(str(DATA[USER_NUMBER]["USING"])[self.x:])
                self.label.show()
                backup_file("make")

    def start_timer(self):
        global BARCODE

        self.barcode = BARCODE

        if FREE_MODE:
            if not self.check_free_mode:
                self.switch_start_label(2)
                self.check_free_mode = 1
        else:
            if self.check_free_mode:
                self.switch_start_label(0)
                self.check_free_mode = 0

        if not BUSY and check_barcode():
            switch_bbr(1)
            write_log("start")

            self.timer.setInterval(1000)
            self.label.setText(str(DATA[USER_NUMBER]["USING"])[self.x:])
            self.nlabel.setText("Пользователь: " + DATA[USER_NUMBER]["NAME"])
            self.nlabel.adjustSize()
            self.nlabel.show()
            self.slabel.hide()
            self.label.show()
            self.change_stop_button()
            self.button.show()
            self.timer.timeout.disconnect()
            self.timer.timeout.connect(self.plus_one_second)
        elif DATA != [] and BARCODE != "" and DATA[USER_NUMBER]["USING"] == "STOP":
            BARCODE = ""
            self.switch_start_label(1)
            QtCore.QTimer.singleShot(3000,
                                     functools.partial(self.switch_start_label, 0))

    def stop_work(self):
        switch_bbr(0)

        write_log("stop")

        self.timer.setInterval(100)
        self.timer.timeout.disconnect()
        self.timer.timeout.connect(self.start_timer)

        def d(self):
            self.slabel.show()
            self.nlabel.hide()
            self.label.hide()
            self.button.hide()

        QtCore.QTimer.singleShot(200, functools.partial(d, self))


application = QtWidgets.QApplication(sys.argv)
win = Window()
win.show()
sys.exit(application.exec())
