
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import PurePath, Path

from bluetooth.ble import BeaconService

import config
import uploader

CONVERSIONS_TEMP = {
    'atemp': 'Lufttemperatur',
    'vtemp': 'Vanntemperatur',
}

CONVERSIONS_PRESS = {
    'apress': 'Lufttrykk'
}

CONVERSIONS_DIR = {
    'wdir': 'Vindretning'
}

OUTDIR = Path.cwd().joinpath('sensordata')


def _process_data(data: dict,
                  validity_delta: timedelta,
                  conversions: dict,
                  file: Path,
                  upload_file: PurePath) -> None:
    try:
        with open(Path, 'r') as fp:
            saved = json.load(fp)
    except FileNotFoundError:
        saved = []

    now = datetime.now()
    new = {}
    new['Tid'] = now.isoformat()

    for k, v in conversions.items():
        try:
            new[v] = data.pop(k)
        except KeyError:
            logging.error(f'Invalid key {k}')
            return

    if len(data.keys()) > 0:
        logging.error(f'Unrecognized keys {",".join(data.keys())}')
        return

    saved.append(new)

    while len(saved) > 0:
        current = saved[0]
        if datetime.fromisoformat(current['Tid']) < now - validity_delta:
            saved.pop(0)
        else:
            break

    with open(file, 'w') as fp:
        json.dump(saved, fp)

    uploader.enqueue(file, upload_file)


@config.tagged('sensors')
def worker(conf: dict) -> None:
    uuid: str = conf.pop('uuid')
    upload_dir = PurePath(conf.pop('upload_dir'))
    validity_delta = timedelta(days=conf.pop('validity_delta_d'))

    for _ in range(3):
        uploader.register()

    if not OUTDIR.exists():
        os.makedirs(OUTDIR, exist_ok=True)

    service = BeaconService()

    while 1:
        devices = service.scan(10)

        print(devices)
