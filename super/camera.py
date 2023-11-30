
import logging
import os
import time
from pathlib import Path, PurePath
from datetime import datetime, timedelta

from picamera2 import Picamera2

import config
import re
import sun
from upload import uploader

IMG_PATH = Path(__file__).parent.parent.joinpath('images')


def _last_image_id(base: Path) -> int:
    """Get the ID of the last image by sorting the images by their last
    modified time

    :param base: Directory containing photos
    :return: ID of last image
    """

    images = sorted((base.joinpath(x) for x in (os.listdir(base))),
                    key=os.path.getmtime, reverse=True)

    if len(images) == 0:
        return 0

    last = images[0].stem
    return int(re.match(r'image_([\d]+)', last).groups()[0])


def _build_relpath(base, offset: int = 0) -> Path:
    """Construct a path object with an ID that is relative to the last image id
    by `offset`. Example is to get the path of the next file, by adding 1 to
    the last saved image.

    :param base: Directory where the images are contained
    :param offset: How much to add to the last image ID
    :return: Path to new image
    """

    return _build_filepath(base,
                           (_last_image_id(base) + offset))


def _build_filepath(base: Path, num: int) -> Path:
    """Construct the path to an image, with name of format `image_00001.jpg`.

    :param base: Directory containing images
    :param num: Image ID
    :return: Path to image
    """
    return base.joinpath(f'image_{str(num).zfill(5)}.jpeg')


def _capture(cam: Picamera2, base: Path) -> None:
    """Capture a new image, and save it to a file that with the ID of the last
    captured image, incremented by 1.


    :param cam: Picamera2 object
    :param base: Directory where images are contained
    """

    path = _build_relpath(base, offset=1)
    cam.capture_file(path)

    logging.info(f'Image saved to {path}')


def _queue_upload(upload_base: PurePath, base: Path) -> None:
    """Queue the upload of the last saved image, uploading it to the remote
    directory `upload_base`.


    :param upload_base: Remote directory where image should be uploaded to
    :param base: Directory where images are contained
    """

    path = _build_relpath(base, offset=0)
    uploader.enqueue(path, upload_base.joinpath(path.stem + path.suffix))


def _td_hours(delta: timedelta) -> int:
    """Convert a `timedelta` to number of hours

    :param delta: Timedelta object
    :return: Number of hours in `delta`
    """
    return delta.seconds // 3600


def _clean_old(img_path: Path) -> None:
    """Clean old photographs. This is done to ensure we never run out of
    storage space. Old photographs are photos older than 30 days.

    :param img_path: Path to where images are contained
    """
    logging.info('Cleaning old photos')

    expiry = datetime.now() - timedelta(days=30)
    images = sorted((img_path.joinpath(x) for x in (os.listdir(img_path))),
                    key=os.path.getmtime, reverse=False)

    while datetime.fromtimestamp(os.path.getmtime(images[0])) < expiry:
        logging.info(f'Removing file {images[0]}')
        os.remove(images.pop(0))


@config.tagged('camera')
def worker(config: dict) -> None:
    """Worker for the camera thread. This captures an image, queues it and
    sleeps for the time specified in `config`, before starting again.


    :param config: Config, usually obtained from super.yml
    """

    img_path = config.pop('outdir', IMG_PATH)
    if isinstance(img_path, str):
        img_path = Path(img_path)

    if not img_path.exists():
        os.makedirs(img_path)

    dst_dir = PurePath(config.pop('upload_dir'))

    sr_margin = config.pop('sr_margin', {'hours': 1})
    ss_margin = config.pop('ss_margin', {'hours': -1})

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
