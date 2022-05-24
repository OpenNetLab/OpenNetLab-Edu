import logging

logger = logging.getLogger(__name__)
try:
    import coloredlogs
    coloredlogs.install(
        level='DEBUG', fmt='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
except ModuleNotFoundError:
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
