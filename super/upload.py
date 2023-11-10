
import logging
import time
from ftplib import FTP
from pathlib import Path, PurePath
from threading import Lock
from typing import Tuple, List
from queue import Queue

import config


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

    def _get_num_entries(self) -> int:
        with self._lock:
            return self._num_entries

    def register(self) -> None:
        with self._lock:
            self._num_entries += 1

    def upload_task(self, ftp_serv: str, ftp_port: int,
                    ftp_user: str, ftp_passwd: str) -> None:

        self._await_register()

        while 1:
            popped: List[Tuple[Path, PurePath]] = []

            while len(popped) < self._get_num_entries():
                popped.append(self._queue.get(block=True))

            with FTP() as ftp:
                ftp.connect(ftp_serv, ftp_port)
                ftp.login(ftp_user, ftp_passwd)

                for src, dst in popped:
                    with open(src, 'rb') as fp:
                        logging.info(f'Uploading {str(src)} to {str(dst)}')
                        ftp.storbinary(f'STOR {str(dst)}', fp)

    def enqueue(self, src: Path, dst: PurePath) -> None:
        self._queue.put_nowait((src, dst))


uploader = _Uploader()


@ config.tagged('upload')
def worker(conf: dict) -> None:
    serv = conf.pop('server')
    port = conf.pop('port')
    user = conf.pop('user')
    passwd = conf.pop('password')

    uploader.upload_task(serv, port, user, passwd)
