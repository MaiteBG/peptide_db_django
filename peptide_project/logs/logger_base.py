import logging as log
import os


def setup_logger(name: str, log_dir: str = './log', level=log.DEBUG) -> log.Logger:
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"{name}.log")

    logger = log.getLogger(name)
    logger.setLevel(level)

    log.basicConfig(format='%(asctime)s: %(levelname)s [%(filename)s:%(lineno)s] %(message)s',
                    datefmt='%I:%M:%S %p',
                    handlers=[
                        log.FileHandler(log_file, encoding='utf-8'),
                        log.StreamHandler()
                    ])

    return logger


def clear_log_file(name: str, log_dir: str = './log'):
    log_file = os.path.join(log_dir, f"{name}.log")
    with open(log_file, 'w') as f:
        f.truncate(0)  # Vacía el archivo


if __name__ == '__main__':
    # clear_log_file()
    setup_logger(__name__)
    log.debug('Mensaje a nivel debug')
    log.info('Mensaje a nivel info')
    log.warning('Mensaje a nivel de warning')
    log.error('Mensaje a nivel de error')
    log.critical('Mensaje a nivel critico')
