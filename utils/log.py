import os
import sys

import logging

def set_logger(file, stdout=False):
    format = '%(asctime)s [%(levelname)s] %(module)s.%(funcName)s %(message)s'

    if stdout:
        stdout_handler = logging.StreamHandler(stream = sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(format))
        stdout_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(format))
    file_handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger(None)
    root_logger.setLevel(logging.DEBUG)
    if stdout:
        root_logger.addHandler(stdout_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger