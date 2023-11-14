
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import PurePath, Path

from serial import Serial

import config
from upload import uploader

CONVERSIONS_TEMP = {
    'AirTemp': 'Lufttemperatur',
    'WaterTemp': 'Vanntemperatur',
}

CONVERSIONS_PRESS = {
    'Pressure': 'Lufttrykk',
}

CONVERSIONS_DIR = {
    'WindDir': 'Vindretning',
    'WindSpeed': 'Vindhastighet',
}

CONVERSIONS_HUMID = {
    'Humidity': 'Fuktighet',
}

OUTDIR = Path.cwd().joinpath('sensordata')


def _process_data(data: dict,
                  validity_delta: timedelta,
                  conversions: dict,
                  file: Path,
                  upload_file: PurePath) -> None:
    try:
        with open(file, 'r') as fp:
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


def _handle_incoming(data: dict, validity_delta: timedelta,
                     upload_dir: PurePath) -> None:

    for conv, file in ((CONVERSIONS_TEMP, 'Temperaturer'),
                       (CONVERSIONS_PRESS, 'Lufttrykk'),
                       (CONVERSIONS_DIR, 'Vind'),
                       (CONVERSIONS_HUMID, 'Fuktighet')):
        _process_data(data, validity_delta, conv, OUTDIR.joinpath(
            f'{file}.json'), upload_dir.joinpath(f'{file}.json'))


@config.tagged('sensors')
def worker(conf: dict) -> None:
    upload_dir = PurePath(conf.pop('upload_dir'))
    validity_delta = timedelta(days=conf.pop('validity_delta_d'))

    if not OUTDIR.exists():
        os.makedirs(OUTDIR)

    ser = Serial('/dev/ttyS0', 115200)
    ser.reset_input_buffer()

    while 1:
        data = bytearray()
        while len(data) == 0 or ser.in_waiting:
            data.extend(ser.read(ser.in_waiting))
            time.sleep(0.1)

        real_data = data.decode()[:-1]
        _handle_incoming(json.loads(real_data), validity_delta, upload_dir)
