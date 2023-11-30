
import logging
from threading import Thread

import camera
import config
import upload
import sensors


def main(conf_file: str) -> None:
    """Main entrypoint for the application. This function loads the config file
    and starts one thread for each of the relevant workers. Each worker is
    passed its entry in the config file as its only argument.

    :param conf_file: Path to config file
    """
    workers = [camera.worker, sensors.worker, upload.worker]
    conf = config.load(conf_file)

    for worker in workers:
        try:
            fname = config.field_name(worker)
        except AttributeError as e:
            raise Exception(
                'Worker must be tagged using @config.tagged') from e

        logging.debug(f'Starting worker thread: {fname}')
        th = Thread(target=worker, args=(conf.pop(fname, {}),))
        th.start()

    # Ensure we dont have a poorly crafted config file.
    conf_remaining = conf.keys()
    if len(conf_remaining) > 0:
        raise Exception(
            f'Unrecognized config field(s) {",".join(conf_remaining)}')

    logging.debug('All threads started successfully')


if __name__ == '__main__':
    import sys
    from argparse import ArgumentParser

    logging.basicConfig(level=logging.DEBUG)

    parser = ArgumentParser()
    parser.add_argument(
        '-c', '--config', default=None, type=str)
    parsed = vars(parser.parse_args(sys.argv[1:]))

    main(parsed['config'])
