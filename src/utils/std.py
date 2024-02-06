import os

def mkdir(dir):
    isExist = os.path.exists(dir)
    if not isExist:
        os.makedirs(dir)