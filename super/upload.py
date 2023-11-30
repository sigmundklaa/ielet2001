
import logging
import time
from ftplib import FTP
from pathlib import Path, PurePath
from threading import Lock
from typing import Tuple, List
from queue import Queue

import config


class _Uploader:
    """Thread safe uploader that allows for queueing of uploads and uploading
    at a later time. This makes it possible for the camera and sensors to be
    uploaded together.
    """
    _num_entries: int
    _queue: Queue
    _lock: Lock

    def __init__(self):
        self._num_entries = 0
        self._queue = Queue()
        self._lock = Lock()

    def _await_register(self) -> None:
        """Wait for a client to register itself with the uploader
        """
        while 1:
            with self._lock:
                if self._num_entries > 0:
                    return

            time.sleep(1)

    def _get_num_entries(self) -> int:
        """Thread safe method of getting the number of clients that have
        registered with the uploader.

        :return: Number of clients registered
        """
        with self._lock:
            return self._num_entries

    def register(self) -> None:
        """Register with the uploader
        """
        with self._lock:
            self._num_entries += 1

    def upload_task(self, ftp_serv: str, ftp_port: int,
                    ftp_user: str, ftp_passwd: str) -> None:
        """Infinitely running upload task, whichs wait for queued uploads
        before uploading them to the server.

        :param ftp_serv: FTP server
        :param ftp_port: FTP port
        :param ftp_user: FTP user
        :param ftp_passwd: FTP password
        """

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
        """Queue an upload

        :param src: Path to file being uploaded
        :param dst: Path on the remote server where the file should be uploaded
        to
        """
        self._queue.put_nowait((src, dst))


uploader = _Uploader()


@ config.tagged('upload')
def worker(conf: dict) -> None:
    """Worker for the uploader thread. This waits for uploads to be queued, and
    then uploads it to the server.

    :param conf: Config object, usually obtained from the super.yml config file
    """

    serv = conf.pop('server')
    port = conf.pop('port')
    user = conf.pop('user')
    passwd = conf.pop('password')

    uploader.upload_task(serv, port, user, passwd)
