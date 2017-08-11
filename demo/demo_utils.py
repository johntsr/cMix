import os
import uuid
import datetime
import random
import string


def createDir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def createFile(fileName, content):
    with open(fileName, 'w') as myFile:
        myFile.write(content)


def moveFile(path1, path2):
    os.rename(path1, path2)


def dateStr():
    now = datetime.datetime.now()
    return unicode(now)


def listDirectories(dir):
    return [subdir for subdir in os.listdir(dir) if os.path.isdir(os.path.join(dir, subdir))]


def listFiles(dir):
    return [file for file in os.listdir(dir) if not os.path.isdir(os.path.join(dir, file))]


def uniqueid():
    return str(uuid.uuid4())


def randomString():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(5, 50)))
