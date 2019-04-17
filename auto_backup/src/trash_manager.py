import os
import time
import shutil
import font_color as FC

from myfile import getSubfolderAndFiles, fileLastModifyTime
from mytime import getStrfTime


class TrashManager():

    EXPIRED_PERIOD = 60 * 60 * 24 * 7
    DATETIME_PATTERN = "%Y-%m-%d_%H:%M:%S"

    def __init__(self, rootPath, expiredPeriod, datetimePattern):
        self.EXPIRED_PERIOD = expiredPeriod
        self.DATETIME_PATTERN = datetimePattern
        self.rootPath = rootPath
        self.expireTime = time.time() - self.EXPIRED_PERIOD

    def deleteExpiredFiles(self):
        """从rootPath开始后序遍历的生成器, 返回(当前路径p,p中所有文件夹名,p中所有文件名)"""
        # [路径, 是否被添加过], 后序遍历防止重复添加
        stack = [[self.rootPath, False]]
        while len(stack):
            curFolderPath, visited = stack[-1]
            folders, files = getSubfolderAndFiles(curFolderPath)
            
            if visited is False and len(folders):
                stack[-1][1] = True
                stack += [[path, False] for path in [os.path.join(curFolderPath, f) for f in list(folders)] ]
            else:
                for f in files:
                    self._checkAndDeleteExpiredFile(os.path.join(curFolderPath, f))
            
                remainItems = os.listdir(curFolderPath)
                # rootPath 不能删除
                if curFolderPath != self.rootPath and len(remainItems) == 0:
                    shutil.rmtree(curFolderPath)
                
                stack.pop()

    def _checkAndDeleteExpiredFile(self, filePath):
        if fileLastModifyTime(filePath) < self.expireTime:
            os.remove(filePath)

    def moveToTrashbin(self, srcPath, srcRootPath):
        assert os.path.exists(srcPath), "被移动文件不存在"

        destRootPathInTrash = self.getDestRootPathInTrash(srcRootPath)
        
        relativePath = srcPath[len(srcRootPath)+1:]
        path = os.path.join(destRootPathInTrash, relativePath)
        l = path.split('/')
        folderPath = '/'.join(l[:-1])
        filename = l[-1]

        if os.path.exists(path):
            shutil.move(srcPath, "{}/{}_{}".format(folderPath, getStrfTime(self.DATETIME_PATTERN), filename))
        else:
            if not os.path.exists(folderPath):
                os.makedirs(folderPath)
            shutil.move(srcPath, path)
        
        print(FC.r("<Trash> ") + path)

    def getDestRootPathInTrash(self, srcRootPath):
        return os.path.join(
                self.rootPath,
                '_'.join(srcRootPath.split('/')) 
                )

if __name__ == "__main__":
    a = TrashManager("/home/mopip77/Desktop/univercity/MintBackup/_cycle_")
    a.deleteExpiredFiles()

        