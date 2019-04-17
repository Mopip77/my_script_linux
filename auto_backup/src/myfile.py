import os
import shutil


def fileLastModifyTime(path):
    stat = os.stat(path)
    return max(
        stat.st_ctime,
        stat.st_mtime
    )

def getSubfolderAndFiles(path):
    folders = set()
    files = set()

    if os.path.isdir(path):
        for i in os.listdir(path):
            if os.path.isdir(os.path.join(path, i)):
                folders.add(i)
            else:
                files.add(i)
    
    return folders, files