
import logging
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

from picamera2 import Picamera2

import config
import sun

IMG_PATH = Path.cwd().joinpath('images')
IMG_CBUF_RANGE = 30


def _last_image_id(base: Path) -> int:
    lastidx = 0
    lasttime = 0

    for i in range(0, IMG_CBUF_RANGE):
        path = _build_filepath(base, i)

        if not path.exists():
            continue

        modtime = os.path.getmtime(path)
        if modtime > lasttime:
            lasttime = modtime
            lastidx = i

    return lastidx


def _build_filepath(base: Path, num: int) -> Path:
    return base.joinpath(f'image_{num}.jpeg')


def _capture(cam: Picamera2, base: Path) -> None:
    path = _build_filepath(base, (_last_image_id(base) + 1) % IMG_CBUF_RANGE)
    cam.capture_file(path)

    logging.info(f'Image saved to {path}')


def _queue_upload(base: Path) -> None:
    pass


def _td_hours(delta: timedelta) -> int:
    return delta.seconds // 3600


@config.tagged('camera')
def worker(config: dict) -> None:
    img_path = config.pop('outdir', IMG_PATH)
    if isinstance(img_path, str):
        img_path = Path(img_path)

    if not img_path.exists():
        os.makedirs(img_path)

    sr_margin = config.pop('sr_margin', {'hours': _td_hours(sun.SR_MARGIN)})
    ss_margin = config.pop('ss_margin', {'hours': _td_hours(sun.SS_MARGIN)})

    sr_margin, ss_margin = timedelta(**sr_margin), timedelta(**ss_margin)

    delay = config.pop('capture_delay_hr', 1/3600)

    cam = Picamera2()
    cam.configure(cam.create_still_configuration())
    cam.start()
    time.sleep(2)

    while 1:
        if sun.is_daytime(datetime.now(), sr_margin, ss_margin):
            _capture(cam, img_path)
            _queue_upload(img_path)

            logging.info('Image captured, upload queued')
        else:
            logging.debug('Not daytime, skipping capture')

        time.sleep(delay * (60 * 60))

    cam.close()
