
import logging
from typing import Any

import config
import sun


def _capture() -> None:
    pass


@config.tagged('camera')
def worker(config: dict) -> None:
    logging.info(f'camera worker started {config}')
    logging.info(f'daytime ?! {sun.is_daytime()}')
    s = sun.sun()
    logging.info(f'sun: {s["sunset"]}, {s["sunrise"]}')
