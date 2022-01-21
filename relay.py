import RPi.GPIO as GPIO


def on_off(switch):
    if switch:
        sw = GPIO.HIGH
    else:
        sw = GPIO.LOW
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(21, GPIO.OUT)
    GPIO.output(pin_number, sw)
