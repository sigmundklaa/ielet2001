
import logging
import os
import time
from pathlib import Path, PureWindowsPath, PurePath
from threading import Lock
from typing import Any, Tuple, List
from queue import Queue

import RPi.GPIO as GPIO
from serial import Serial

import config

GPIO_POWER_PIN = 6
NEWLINE = '\r\n'
AT_OK = 'OK' + NEWLINE


class Modem:
    _ser: Serial

    def __init__(self):
        self._ser = Serial('/dev/ttyS0', 115200, timeout=5)

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(GPIO_POWER_PIN, GPIO.OUT)
        time.sleep(0.1)
        GPIO.output(GPIO_POWER_PIN, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(GPIO_POWER_PIN, GPIO.LOW)
        time.sleep(5)  # Allow it to boot. 20 sec is prob overkill

        self._ping()

    def _ping(self) -> None:
        self._write('AT\r\n'.encode())

        read = self._ser.read(20)
        print(read)
        if len(read) == 0:
            raise Exception('Timed out')
        elif not read.decode().lstrip().endswith(AT_OK):
            raise Exception('Not ok')

    def _read_response(self, byte_delay_s: int = 0.1) -> bytes:
        bread = bytes()
        time.sleep(byte_delay_s)

        while self._ser.inWaiting():
            bread += self._ser.read(self._ser.inWaiting())
            time.sleep(byte_delay_s)

        return bread

    def _send_cmd(self, cmd: str, *values: Any) -> None:
        values = list(values).copy()

        if len(values) > 0:
            for idx, value in enumerate(values):
                if isinstance(value, str) and value not in ',?':
                    value = f'"{value}"'
                else:
                    value = str(value)

                values[idx] = value

            values = ['='] + values
        else:
            values = []

        data = f'AT+{cmd}{"".join(values)}{NEWLINE}'

        self._write(data.encode())
        print(self._read_response())

    def _write(self, data: bytes) -> None:
        print(data)
        self._ser.write(data)

    def ftp_login(self, serv: str, port: int, user: str, pwd: str) -> None:
        """TODO: mode, type?"""
        self._send_cmd('CFTPSSTART')
        self._send_cmd('CFTPSLOGIN', serv, ',', port, ',', user, ',', pwd)
        time.sleep(0.5)

    def ftp_logout(self):
        self._send_cmd('CFTPSLOGOUT')
        time.sleep(0.5)
        self._send_cmd('CFTPSSTOP')

    def ftp_upload(self, path: str):
        # TODO: necessary?
        if not path.endswith('\\'):
            path += '\\'

        self._send_cmd('CFTPSPUTFILE', path, 3)

    def ftransfer_tx(self, src: Path, dst: str):
        size = os.path.getsize(src)
        self._send_cmd('CFTRANRX',
                       str(PureWindowsPath('E:').joinpath(dst)), size)

        with open(src, 'rb') as fp:
            for _ in range(0, size):
                self._write(fp.read(1))
                time.sleep(1/((115200/8) + 1000))

        self._write(NEWLINE.encode())
        print(self._read_response())


class _Uploader:
    _num_entries: int
    _queue: Queue
    _lock: Lock

    def __init__(self):
        self._num_entries = 0
        self._queue = Queue()
        self._lock = Lock()

    def _await_register(self) -> None:
        while 1:
            with self._lock:
                if self._num_entries > 0:
                    return

            time.sleep(1)

    def register(self) -> None:
        with self._lock:
            self._num_entries += 1

    def upload_task(self, modem: Modem) -> None:
        self._await_register()

        while 1:
            popped: List[Tuple[Path, PurePath]] = []

            while len(popped) < self._num_entries:
                popped.append(self._queue.get(block=True))

            for src, dst in popped:
                logging.info(f'Uploading {str(src)} to {str(dst)}')
                modem.ftransfer_tx(src, dst.stem + dst.suffix)
                modem.ftp_upload(str(dst))

    def enqueue(self, src: Path, dst: PurePath) -> None:
        self._queue.put_nowait((src, dst))


uploader = _Uploader()


@config.tagged('upload')
def worker(conf: dict) -> None:
    serv = conf.pop('server')
    port = conf.pop('port')
    user = conf.pop('user')
    passwd = conf.pop('password')

    modem = Modem()
    modem.ftp_logout()

    try:
        modem.ftp_login(serv, port, user, passwd)
    except Exception as e:
        modem.ftp_logout()
        raise e

    uploader.upload_task(modem)
