
import time
from typing import Any

import RPi.GPIO as GPIO
from serial import Serial

import config

GPIO_POWER_PIN = 6


class Modem:
    _ser: Serial

    def __init__(self):
        self._ser = Serial('/dev/ttyS0', 115200, timeout=1)

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(GPIO_POWER_PIN, GPIO.OUT)
        time.sleep(0.1)
        GPIO.output(GPIO_POWER_PIN, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(GPIO_POWER_PIN, GPIO.LOW)
        time.sleep(10)  # Allow it to boot. 20 sec is prob overkill

        self._ping()

    def _ping(self) -> None:
        self._write('AT\r\n'.encode())

        read = self._ser.read()
        print(read)
        if len(read) == 0:
            raise Exception('Timed out')
        elif not read.decode().endswith('OK'):
            raise Exception('Not ok')

    def _send_cmd(self, cmd: str, *values: Any) -> None:
        values = list(values.copy())

        for idx, value in enumerate(values):
            if value is None:
                value = '?'
            elif isinstance(value, str) and value != ',':
                value = f'"{value}"'

            values[idx] = value

        data = f'AT+{cmd}={"".join(values)}\r\n'
        print(data)

        self._write(cmd.encode())
        print(self._ser.read())

    def _write(self, data: bytes) -> None:
        self._ser.write(data)


@config.tagged('upload')
def worker(conf: dict) -> None:
    if 0:
        serv = conf.pop('server')
        port = conf.pop('port')
        user = conf.pop('user')
        passwd = conf.pop('password')

    modem = Modem()
