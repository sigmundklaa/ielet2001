
import logging
import os
import time
from pathlib import Path, PurePath
from datetime import datetime, timedelta

from picamera2 import Picamera2

import config
import sun
from upload import uploader

IMG_PATH = Path(__file__).parent.parent.joinpath('images')
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


def _build_relpath(base, offset: int = 0) -> Path:
    return _build_filepath(base,
                           (_last_image_id(base) + offset) % IMG_CBUF_RANGE)


def _build_filepath(base: Path, num: int) -> Path:
    return base.joinpath(f'image_{str(num).zfill(5)}.jpeg')


def _capture(cam: Picamera2, base: Path) -> None:
    path = _build_relpath(base, offset=1)
    cam.capture_file(path)

    logging.info(f'Image saved to {path}')


def _queue_upload(upload_base: PurePath, base: Path) -> None:
    path = _build_relpath(base, offset=0)
    uploader.enqueue(path, upload_base.joinpath(path.stem + path.suffix))


def _td_hours(delta: timedelta) -> int:
    return delta.seconds // 3600


def _clean_old(img_path: Path) -> None:
    logging.info('Cleaning old photos')

    expiry = datetime.now() - timedelta(days=30)
    images = sorted((img_path.joinpath(x) for x in (os.listdir(img_path))),
                    key=os.path.getmtime, reverse=False)

    while datetime.fromtimestamp(os.path.getmtime(images[0])) < expiry:
        logging.info(f'Removing file {images[0]}')
        os.remove(images.pop(0))


@config.tagged('camera')
def worker(config: dict) -> None:
    img_path = config.pop('outdir', IMG_PATH)
    if isinstance(img_path, str):
        img_path = Path(img_path)

    if not img_path.exists():
        os.makedirs(img_path)

    dst_dir = PurePath(config.pop('upload_dir'))

    sr_margin = config.pop('sr_margin', {'hours': _td_hours(sun.SR_MARGIN)})
    ss_margin = config.pop('ss_margin', {'hours': _td_hours(sun.SS_MARGIN)})

    sr_margin, ss_margin = timedelta(**sr_margin), timedelta(**ss_margin)

    delay = config.pop('capture_delay_hr', 1)

    cam = Picamera2()
    cam.configure(cam.create_still_configuration())
    cam.options['quality'] = config.pop('quality', 85)
    cam.start()
    time.sleep(2)

    uploader.register()

    while 1:
        if sun.is_daytime(datetime.now(), sr_margin, ss_margin):
            _capture(cam, img_path)
            _queue_upload(dst_dir, img_path)

            logging.info('Image captured, upload queued')

            _clean_old(img_path)
        else:
            logging.debug('Not daytime, skipping capture')

        time.sleep(delay * (60 * 60))

    cam.close()
