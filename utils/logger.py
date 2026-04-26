import logging
import os
import datetime


DIR = 'logs'

os.makedirs(DIR,exist_ok =True)

log_file = os.path.join(DIR,f"{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log")


logging.basicConfig(
    filename = log_file,
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)


def get_logger(name):

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger

