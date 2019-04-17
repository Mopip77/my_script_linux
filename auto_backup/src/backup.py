import os
import shutil
import time
import yaml

import font_color as FC

from multiprocessing import Pool
from mytime import getStrfTime
from myfile import fileLastModifyTime, getSubfolderAndFiles
from trash_manager import TrashManager

class BackUpUtil():

    rootPath = '/'.join( os.path.realpath(__file__).split('/')[:-2] )
    
    configPath=  os.path.join(rootPath, 'config.yaml')
    referencePath = os.path.join(rootPath, 'folder_reference.txt')

    def __init__(self):
        self.dateTimePattern = None
        self.defaultDestPath = None
        self.trashPath = None
        self.expiredPeriod = None
        self._loadConfig()
        self.folderRefernece = self._getFolderReference()
        self.updatedFolderRenference = []

        self.trashManager = TrashManager(self.trashPath, self.expiredPeriod, self.dateTimePattern)

    def _loadConfig(self):
        with open(self.configPath, 'r') as f:
            config = f.read()
        config = yaml.load(config)

        self.dateTimePattern = config['DATETIME_PATTERN']
        self.defaultDestPath = config['DEFAULT_DESTPATH']
        self.trashPath = config['TRASH_FOLDER_PATH']
        self.expiredPeriod = config['EXPIRED_PERIOD']
        
    def _getFolderReference(self):
        folderRefernece = []
        with open(self.referencePath, 'r') as f:
            for line in f.readlines():
                line = line.split('\n')[0]
                if line == '':
                    continue
                    
                items = line.split(',')
                _src, _dest = items[:2]
                _time = None
                if items.__len__() > 2:
                    t_arr = time.strptime(items[2], self.dateTimePattern)
                    _time = time.mktime(t_arr)

                folderRefernece.append([_src, _dest, _time])
        return folderRefernece

    def _updateFolderReference(self):
        with open(self.referencePath, 'w') as f:
            for line in self.updatedFolderRenference:
                text = ','.join(line) + '\n'
                f.write(text)

    def _appendFolderReference(self, srcPath, destPath):
        with open(self.referencePath, 'a') as f:
            text = ','.join([srcPath, destPath]) + '\n'
            f.write(text)

    def _desktopNotify(self):
        text = '\n'.join([_[0] for _ in self.folderRefernece])
        title = "备份完成,同步了{}个文件夹".format(len(self.folderRefernece))
        os.system('notify-cron -t 5000 "{}" "{}"'.format(title, text))

    def _syncFiles(self, curSrcPath, srcFiles, curDestPath, destFiles, lastSyncTime, destRootPath):
        """同步curSrcPath文件夹的所有文件到目标文件夹同级的位置"""
        uselessFiles = destFiles.difference(srcFiles)
        newFiles = srcFiles.difference(destFiles)
        
        # 目标文件夹无用文件
        for f in uselessFiles:
            print(FC.r("[Del ] ") + f)
            self.trashManager.moveToTrashbin(os.path.join(curDestPath, f), destRootPath)

        # 新增文件
        for f in newFiles:
            print(FC.y("[New ] ") + f)
            shutil.copy(
                os.path.join(curSrcPath, f),
                os.path.join(curDestPath, f)
                )

        # 都有的文件
        for f in destFiles.intersection(srcFiles):
            _src_f = os.path.join(curSrcPath, f)
            _dest_f = os.path.join(curDestPath, f)

            if lastSyncTime is not None:
                if fileLastModifyTime(_src_f) <= lastSyncTime:
                    continue
                else:
                    self._syncFile(_src_f, _dest_f, destRootPath)
            else:
                self._syncFile(_src_f, _dest_f, destRootPath)

    def _syncFile(self, srcFile, destFile, destRootPath):
        """比较并同步单个文件"""
        # 大小不同直接复制
        if os.stat(srcFile).st_size != os.stat(destFile).st_size:
            print(FC.r("[Diff] ") + srcFile.split('/')[-1])
            self.trashManager.moveToTrashbin(destFile, destRootPath)
            shutil.copy(srcFile, destFile)
            return

        with open(srcFile, 'rb') as f1, open(destFile, 'rb') as f2:
            while True:
                data1 = f1.read(4096)
                data2 = f2.read(4096)
                if data1 != data2:
                    self.trashManager.moveToTrashbin(destFile, destRootPath)
                    shutil.copy(srcFile, destFile)
                    print(FC.r("[Diff] ") + srcFile.split('/')[-1])
                    return
                elif data1 == b'':
                    print(FC.g("[Same] ") + srcFile.split('/')[-1])
                    return

    def _syncFolders(self, srcFolders, curDestPath, destFolders, destRootPath):
        """更新当前文件夹下所有文件夹,仅删除,不涉及文件夹内文件的修改"""
        uselessFolders = destFolders.difference(srcFolders)

        for f in uselessFolders:
            self.trashManager.moveToTrashbin(os.path.join(curDestPath, f), destRootPath)

    def _handleFolder(self, folderReference, trace):
        """同步当前传入的folderReference"""
        srcPath, destPath, lastSyncTime = folderReference

        srcQueue = [trace]
        # 循环遍历,不用递归了
        while srcQueue.__len__() > 0:
            trace = srcQueue.pop()
            # 当前匹配路径
            curSrcPath = os.path.join(srcPath, trace)
            curDestPath = os.path.join(destPath, trace)
            
            # 文件夹内部文件改变,文件夹的修改时间并不会变,所以以此判断可能会造成漏判
            print(FC.c("check: {}").format(curSrcPath))            

            if not os.path.isdir(curDestPath):
                os.makedirs(curDestPath)
            # 获得源,目标路径文件夹和文件
            srcFolders, srcFiles = getSubfolderAndFiles(curSrcPath)
            destFolders, destFiles = getSubfolderAndFiles(curDestPath)
            # 比对更新当前文件夹下所有文件夹
            self._syncFolders(srcFolders, curDestPath, destFolders, destPath)
            # 比对更新当前文件夹下所有文件
            self._syncFiles(curSrcPath, srcFiles, curDestPath, destFiles, lastSyncTime, destPath)
            # 进入下个文件夹
            srcQueue.extend([os.path.join(trace, srcF) for srcF in srcFolders])

    def _checkSameInReference(self, path, field):
        for line in self.folderRefernece:
            _src, _dest = line[:2]
            if field == 'src' and _src == path:
                return True
            elif field == 'dest' and _dest == path:
                return True
        return False

    def _checkAndDeleteFormerPath(self, path):
        """删除修改前(被弃用)的文件夹路径"""
        if not os.path.isdir(path):
            return
        while True:
            
            print(("是否删除被弃置的文件夹[" + FC.g("{}") + "]?[y/N]").format(path))
            check = input().strip()

            if check == '' or check.upper() == 'N':
                return
            elif check.upper() == 'Y':
                shutil.rmtree(path)
                
                print(FC.r("文件夹已删除"))
                return

    def sync(self, n_jobs=4):
        pool = Pool(n_jobs)

        self.updatedFolderRenference = [fr[:2] + [getStrfTime(self.dateTimePattern)] for fr in self.folderRefernece]
        jobs = [pool.apply_async(self._handleFolder, args=(fr, '')) for fr in self.folderRefernece]
        [j.get() for j in jobs]
        
        # 写回folderRenference
        self._updateFolderReference()
        # 桌面提醒
        self._desktopNotify()

    def addNewReference(self):
        print("请输入备份源文件夹路径:")
        srcPath = input()
        while not os.path.isdir(srcPath):
            print("\n该地址不是有效的文件夹,请输入备份源文件夹路径:")
            srcPath = input()
        
        assert not self._checkSameInReference(srcPath, 'src'), "路径已存在在当前备份中"
        
        
        print(("\n请输入备份目标文件夹根路径\n(留空则用默认路径)[" + FC.y("{}") + "]:").format(self.defaultDestPath))
        destPath = input()
        if destPath.strip() == '':
            destPath = self.defaultDestPath
        if not os.path.isdir(destPath):
            os.makedirs(destPath)
        
        srcFolderName = os.path.realpath(srcPath).split('/')[-1]
        print(("\n请输入备份目标文件夹名\n(留空则用源文件夹名)[" + FC.y("{}") + "]:").format(srcFolderName))
        destFolderName = input()
        if destFolderName.strip() == '':
            destFolderName = srcFolderName
        
        while os.path.isdir(os.path.join(destPath, destFolderName)):
            print("\n目标文件夹下已有同名文件夹,换个名字:")
            destFolderName = input()
        
        destPath = os.path.join(destPath, destFolderName)
        os.makedirs(destPath)

        self._appendFolderReference(srcPath, destPath)
        print("\n" + FC.g("添加成功") + "\n原路径:{}\n目标路径:{}".format(srcPath, destPath))

    def delRenference(self):
        print(FC.w("当前备份文件夹信息:", 'c') + "\n")
        for idx, ref in enumerate(self.folderRefernece):
            print((FC.g('[{}]') + " {}\n     {}\n").format(str(idx).zfill(2), ref[0], ref[1]))
        
        print(FC.r('请输入要删除的序号:'))
        idx = input()

        try:
            _idx = int(idx)
            assert _idx < len(self.folderRefernece), '序号超出范围'

            srcPath, destPath = self.folderRefernece[_idx][:2]
            
            for idx, fr in enumerate(self.folderRefernece):
                if idx == _idx:
                    continue

                if fr[2] is None:
                    self.updatedFolderRenference.append(fr[:2])
                else:
                    self.updatedFolderRenference.append(fr[:2] + [getStrfTime(self.dateTimePattern, fr[2])])
            self._updateFolderReference()
            print("删除完毕")
            self._checkAndDeleteFormerPath(srcPath)
            self._checkAndDeleteFormerPath(destPath)
            self._checkAndDeleteFormerPath(self.trashManager.getDestRootPathInTrash(destPath))
        except:
            print('序号不合规范')

    def modifyRenference(self):
        print(FC.white("当前备份文件夹信息:", 'c') + '\n')
        for idx, ref in enumerate(self.folderRefernece):
            print((FC.g("[{}]") + " {}\n     {}\n").format(str(idx).zfill(2), ref[0], ref[1]))
        
        idx = input(FC.r("请输入要修改的序号:"))

        try:
            _idx = int(idx)
            assert _idx < len(self.folderRefernece), '序号超出范围'

            print("\n" + FC.g("待修改项:") + "\n原路径:{}\n目标路径:{}\n".format(self.folderRefernece[_idx][0], self.folderRefernece[_idx][1]))
            print(FC.g("[1]") + "修改原路径")
            print(FC.g("[2]") + "修改目标路径")
            modifyField = int(input(FC.c("请输入修改项:")))
            
            srcPath, destPath = self.folderRefernece[_idx][:2]
            formerSrcPath = srcPath
            formerDestPath = destPath

            #modifyField = int(input())
            if modifyField == 1:
                # 修改原路径
                print("请输入备份原文件夹路径:")
                srcPath = input()

                while not os.path.isdir(srcPath):
                    print("\n该地址不是有效的文件夹,请输入备份源文件夹路径:")
                    srcPath = input()
        
                if srcPath == formerSrcPath:
                    print("文件夹未变动")     
                
                # 源文件夹可以被多次映射
                # assert not self._checkSameInReference(srcPath, 'src'), "路径已存在在当前备份中" 
                
            else:
                # 修改目标路径
                _t = True
                while _t:
                    print("\n请输入备份目标文件夹绝对路径:")
                    destPath = input()
                    if not os.path.isdir(destPath):
                        os.makedirs(destPath)
                        _t = False
                    else:
                        _i = input("该文件夹非空,使用则清空文件夹,确认使用吗?[y/N]")
                        if _i.strip() == '' or _i.strip().upper() == 'N':
                            continue
                        elif _i.upper() == 'Y':
                            _t = False
                        else:
                            print("输入有误")

                if destPath != formerDestPath:
                    assert not self._checkSameInReference(destPath, 'dest'), "路径已存在在当前备份中"

                    drpit = self.trashManager.getDestRootPathInTrash(formerDestPath)
                    if os.path.exists(drpit):
                        shutil.move(
                            drpit,
                            self.trashManager.getDestRootPathInTrash(destPath)
                        )

                else:
                    print("文件夹未变动")
                    return    

            for fr in self.folderRefernece:
                if fr[2] is None:
                    self.updatedFolderRenference.append(fr[:2])
                else:
                    self.updatedFolderRenference.append(fr[:2] + [getStrfTime(self.dateTimePattern, fr[2])])
            self.updatedFolderRenference[_idx] = [srcPath, destPath]
            self._updateFolderReference()
            print("更新完毕")
            self._checkAndDeleteFormerPath( (formerSrcPath, formerDestPath)[modifyField - 1] )
        except AssertionError as e:
            print(e)
        except:
            print('序号不合规范')

    def display(self):
        if len(self.folderRefernece) == 0:
            
            print(FC.w("当前还没有正在备份的文件夹", 'g') + "\n")
        else:
            print(FC.w("当前备份文件夹信息:", 'c') + "\n")
            for idx, ref in enumerate(self.folderRefernece):
                if ref[2] is None:
                    print((FC.g("[{}]") + " Src : {}\n     Dest: {}\n     " + FC.y("尚未备份") + "\n").format(str(idx).zfill(2), ref[0], ref[1]))
                else:
                    print( (FC.g("[{}]") + " Src : {}\n     Dest: {}\n     最后备份时间:" + FC.y("[{}]") + "\n").format(
                        str(idx).zfill(2), ref[0], ref[1], getStrfTime(self.dateTimePattern, ref[2]) ))

    def run(self, n_jobs=4):
        self.sync(n_jobs)
        self.trashManager.deleteExpiredFiles()

    def test(self):
        self.updatedFolderRenference = [fr[:2] + [getStrfTime(self.dateTimePattern)] for fr in self.folderRefernece]
        
        # for fr in self.folderRefernece:
        self._handleFolder(self.folderRefernece[2], "")
        
        # 写回folderRenference
        self._updateFolderReference()
        # 桌面提醒
        self._desktopNotify()

if __name__ == "__main__":
    buu = BackUpUtil()
    buu.test()
    # buu.delRenference()