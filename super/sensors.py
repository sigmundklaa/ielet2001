
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import PurePath, Path

from serial import Serial

import config
from upload import uploader

# Time format: day/month,hour
TIME_FORMAT = '%d/%m,%H'

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

OUTDIR = Path(__file__).parent.parent.joinpath('sensordata')


def _process_data(data: dict,
                  validity_delta: timedelta,
                  conversions: dict,
                  file: Path,
                  upload_file: PurePath) -> None:
    """Processes new data, by adding a timestamp and filtering out old
    measurements from the appropriate file, before queueing its upload to the
    remote server.

    :param data: Newly recieved data
    :param validity_delta: timedelta object that specifies how long old
    measurements are valid.
    :param conversions: Dictionary containing mappings between the fields from
    the sensors and the expected field names on the server.
    :param file: File to save to. This file is also the one being uploaded to
    the server.
    :param upload_file: Path to where the file should be saved on the remote.
    """
    try:
        with open(file, 'r') as fp:
            saved = json.load(fp)
    except FileNotFoundError:
        saved = []

    now = datetime.now()
    new = {}
    new['Tid'] = now.strftime(TIME_FORMAT)

    # The conversion object in practice does two things:
    # 1) converts the field name recieved in the object from the sensors to the
    #    expected name on the server.
    # 2) determines which fields should be saved to which file. Since we are
    #    passing in the full `data` object, and only poppping of those we need
    #    for this config, we dont need to manually filter out those that are
    #    not relevant to this file.
    for k, v in conversions.items():
        try:
            new[v] = data.pop(k)
        except KeyError:
            logging.error(f'Invalid key {k}')
            return

    saved.append(new)
    now = datetime.strptime(now.strftime(TIME_FORMAT), TIME_FORMAT)

    # Remove old measurements as they are no longer relevant for being
    # displayed on the server.
    while len(saved) > 0:
        current = saved[0]
        if datetime.strptime(current['Tid'], TIME_FORMAT) < now - validity_delta:
            saved.pop(0)
            logging.debug('Popping old measurement')
        else:
            break

    with open(file, 'w') as fp:
        json.dump(saved, fp)

    uploader.enqueue(file, upload_file)


def _handle_incoming(data: dict, validity_delta: timedelta,
                     upload_dir: PurePath) -> None:
    """Handle incoming data by associating the conversion dictionaries with
    their respective filenames, and then calling `_process_data`.

    :param dict: Newly recieved data
    :param validity_delta: timedelta object specifying validity of old
    measurements.
    :param upload_dir: Path to remote directory the files should be uploaded
    to.
    """
    for conv, file in ((CONVERSIONS_TEMP, 'Temperaturer'),
                       (CONVERSIONS_PRESS, 'Lufttrykk'),
                       (CONVERSIONS_DIR, 'Vind'),
                       (CONVERSIONS_HUMID, 'Fuktighet')):
        _process_data(data, validity_delta, conv, OUTDIR.joinpath(
            f'{file}.json'), upload_dir.joinpath(f'{file}.json'))


@config.tagged('sensors')
def worker(conf: dict) -> None:
    """Worker thread for the sensors. This thread listens for new data coming
    in on the serial port, processes it and then queues its upload to the
    remote server.

    :param conf: Config object, usually objtained from the super.yml config
    file.
    """
    upload_dir = PurePath(conf.pop('upload_dir'))
    validity_delta = timedelta(days=conf.pop('validity_delta_d'))

    if not OUTDIR.exists():
        os.makedirs(OUTDIR)

    ser = Serial('/dev/ttyS0', 115200)

    # Reset input buffer. Old data remaining in the buffer can be corrupt,
    # which could break out JSON parser.
    ser.reset_input_buffer()

    while 1:
        data = bytearray()
        while len(data) == 0 or ser.in_waiting:
            data.extend(ser.read(ser.in_waiting))
            time.sleep(0.1)

        real_data = data.decode()[:-1]
        logging.debug(f'Read data: {real_data}')
        _handle_incoming(json.loads(real_data), validity_delta, upload_dir)
