from datetime import datetime as dt, timedelta
from PyQt5 import QtCore, QtGui, QtWidgets
from scan import b_read
import socket
import json
import time
import threading
import sys
import functools
from pyautogui import sizeq

BARCODE = ""

DATA = []

BUSY = 0

N = 0


def check_barcode():
    global DATA
    global N

    if DATA == [] or BARCODE == "":
        return False

    for i in range(len(DATA)):
        if DATA[i]["BARCODE"] == BARCODE:
            N = i
            break
        return False
    date = str(dt.today()).split()
    date[1] = date[1].split(":")
    time = timedelta(hours=int(date[1][0]), minutes=int(date[1][1]))

    a = date[0] == DATA[N]["DATE"]
    b = DATA[N]["TIME"][0] <= time < DATA[N]["TIME"][1]

    if a and b:
        if "USING" not in DATA[N].keys():
            DATA[N]["USING"] = timedelta(minutes=10)
            return True
        elif DATA[N]["USING"] != "STOP":
            return True
    return False


def listen_port(port: int):

    def sub_listen(port):
        global DATA
        sock = socket.socket()
        sock.bind(("", port))

        while True:
            sock.listen(1)
            conn, addr = sock.accept()
            data = conn.recv(4096)

            get = json.loads(data)

            for i in range(len(get)):
                h0 = get[i]["TIME"][0]["hours"]
                m0 = get[i]["TIME"][0]["minutes"]
                h1 = get[i]["TIME"][1]["hours"]
                m1 = get[i]["TIME"][1]["minutes"]

                get[i]["TIME"][0] = timedelta(hours=h0, minutes=m0)
                get[i]["TIME"][1] = timedelta(hours=h1, minutes=m1)

            if get not in DATA:
                DATA.extend(get)

    listen = threading.Thread(target=sub_listen, args=(port,))
    listen.daemon = True
    listen.start()


def read_barcode():

    def sub_read():
        global BARCODE
        while True:
            data = b_read()
            BARCODE = "".join([i for i in data if i.isdigit()])

    reader = threading.Thread(target=sub_read)
    reader.daemon = True
    reader.start()


class Window(QtWidgets.QWidget):
    global BARCODE

    def __init__(self):
        super().__init__()

        listen_port(9003)

        read_barcode()

        # self.setCursor(QtCore.Qt.BlankCursor)

        self.set_timer()

        self.set_stop_button()

        self.set_name_label()

        self.set_start_label()

        self.showFullScreen()

    def on_click(self):
        global BARCODE
        global BUSY
        BARCODE = ""
        BUSY = 0

        self.timer.setInterval(300)
        self.timer.timeout.disconnect()
        self.timer.timeout.connect(self.start_timer)

        def d(self):
            self.slabel.show()
            self.nlabel.hide()
            self.label.hide()
            self.button.hide()

        self.change_stop_button(1)
        QtCore.QTimer.singleShot(200, functools.partial(d, self))
        QtCore.QTimer.singleShot(400,
                                 functools.partial(self.change_stop_button, 0))

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            sys.exit()

    def set_stop_button(self):
        self.button = QtWidgets.QPushButton('Стоп', self)
        self.button.setGeometry(155, 200, 170, 85)
        self.button.setFont(QtGui.QFont('Times New Roman', 30))
        self.button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.button.clicked.connect(self.on_click)
        self.button.setStyleSheet('QPushButton {border-radius: \
                                    40px 40px 40px 40px; border:\
                                     15px #c284c0; background-color:\
                                      #c284c0;  color: black;}')
        self.button.hide()

    def change_stop_button(self, mode: int):
        a = 'QPushButton {border-radius: \
                40px 40px 40px 40px; border:\
                    15px #c284c0; background-color:\
                        #c284c0;  color: black;}'

        b = 'QPushButton {border-radius: \
                40px 40px 40px 40px; border:\
                    15px #84c295; background-color:\
                        #84c295;  color: black;}'
        if mode:
            self.button.setStyleSheet(b)
            self.button.show()
        else:
            self.button.setStyleSheet(a)

    def set_timer(self):
        self.s = size()
        self.label = QtWidgets.QLabel(self)
        self.label.move(int(self.s[0]/5.2), int(self.s[1]/6))
        self.label.setFont(QtGui.QFont('Arial', 90))
        self.label.setText(str(timedelta(minutes=10))[2:])
        self.label.adjustSize()
        self.label.hide()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.start_timer)
        self.timer.start()

    def set_name_label(self):
        self.nlabel = QtWidgets.QLabel(self)
        self.nlabel.move(20, 12)
        self.nlabel.setFont(QtGui.QFont('Times New Roman', 13))

    def set_start_label(self):
        self.slabel = QtWidgets.QLabel(self)
        self.slabel.move(20, 120)
        self.slabel.setFont(QtGui.QFont('Times New Roman', 30))
        self.slabel.setText("Отсканируйте штрих-код")
        self.slabel.adjustSize()
        self.slabel.show()

    def switch_start_label(self, mode: int):
        if mode:
            self.slabel.setText("Время вышло!")
            self.slabel.move(60, 120)
            self.slabel.adjustSize()
            self.slabel.show()
        else:
            self.slabel.move(20, 120)
            self.slabel.setText("Отсканируйте штрих-код")
            self.slabel.adjustSize()
            self.slabel.show()

    def plus_one_second(self):
        if DATA[N]["USING"] == timedelta(seconds=0):
            DATA[N]["USING"] = "STOP"
            self.on_click()
        elif DATA[N]["USING"] != "STOP":
            DATA[N]["USING"] -= timedelta(seconds=1)
            self.label.setText(str(DATA[N]["USING"])[2:])
            self.label.show()

    def start_timer(self):
        global BUSY
        global BARCODE

        if not BUSY and check_barcode():
            self.timer.setInterval(1000)
            self.label.setText(str(DATA[N]["USING"])[2:])
            self.nlabel.setText("Пользователь: " + DATA[N]["NAME"])
            self.nlabel.adjustSize()
            self.nlabel.show()
            self.slabel.hide()
            self.label.show()
            self.button.show()
            self.timer.timeout.disconnect()
            self.timer.timeout.connect(self.plus_one_second)
            BUSY = 1
        elif DATA != [] and BARCODE != "" and DATA[N]["USING"] == "STOP":
            BARCODE = ""
            self.switch_start_label(1)
            QtCore.QTimer.singleShot(3000,
                                     functools.partial(self.switch_start_label, 0))


application = QtWidgets.QApplication(sys.argv)
win = Window()
win.show()
sys.exit(application.exec())
