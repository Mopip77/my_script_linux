import os
import shutil
import time

import font_color as FC


class BackUpUtil():

    referencePath = '/'.join(
        os.path.realpath(__file__).split('/')[:-1] + ['folder_reference.txt']
    )

    dateTimePatten = "%Y-%m-%d %H:%M:%S"

    defaultDestPath = "/home/mopip77/Desktop/univercity/MintBackup"

    def __init__(self):
        self.folderRefernece = self._getFolderReference()
        self.updatedFolderRenference = []

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
                    t_arr = time.strptime(items[2], self.dateTimePatten)
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
        os.system('notify-send -t 5000 "{}" "{}"'.format(title, text))

    def _getStrfTime(self, t=None):
        if t is None:
            return time.strftime(self.dateTimePatten, time.localtime())
        else:
            t = time.localtime(t)
            return time.strftime(self.dateTimePatten, t)

    def _getSubfolderAndFiles(self, path):
        folders = set()
        files = set()

        for i in os.listdir(path):
            if os.path.isdir(os.path.join(path, i)):
                folders.add(i)
            else:
                files.add(i)
        
        return folders, files

    def _delItem(self, itemPath):
        if os.path.exists(itemPath):
            if os.path.isdir(itemPath):
                shutil.rmtree(itemPath)
            else:
                os.remove(itemPath)

    def _cleanOnlyExistInDest(self, srcItems, destItems, destPath):
        useless = destItems.difference(srcItems)
        for u in useless:
            
            print(FC.r("[Del ] ") + u)
            self._delItem(os.path.join(destPath, u))
        
        destItems = destItems.intersection(srcItems)
        return destItems

    def _copyFile(self, curPath, destPath):
        shutil.copy(curPath, destPath)

    def _syncFiles(self, curSrcPath, srcFiles, curDestPath, destFiles, lastSyncTime):
        newFiles = srcFiles.difference(destFiles)
        for f in newFiles:
            print(FC.y("[New ] ") + f)
            self._copyFile(
                os.path.join(curSrcPath, f),
                os.path.join(curDestPath, f)
                )

        # 都有的文件
        for f in destFiles:
            _src_f = os.path.join(curSrcPath, f)
            _dest_f = os.path.join(curDestPath, f)

            if lastSyncTime is not None:
                # 不知道这几个时间具体区别,直接找最近的
                nearestTime = max([
                    os.path.getctime(_src_f),
                    os.path.getmtime(_src_f),
                ])

                if nearestTime <= lastSyncTime:
                    continue
                else:
                    self._syncFile(_src_f, _dest_f)
            else:
                self._syncFile(_src_f, _dest_f)

    def _syncFile(self, srcFile, destFile):
        with open(srcFile, 'rb') as f1, open(destFile, 'rb') as f2:
            while True:
                data1 = f1.read(1024)
                data2 = f2.read(1024)
                if data1 != data2:
                    self._copyFile(srcFile, destFile)
                    print(FC.r("[Diff] ") + srcFile.split('/')[-1])
                    return
                elif data1 == b'':
                    print(FC.g("[Same] ") + srcFile.split('/')[-1])
                    return

    def _handleFolder(self, folderRefernece, trace):
        srcPath, destPath, lastSyncTime = folderRefernece

        srcQueue = [trace]
        # 循环遍历,不用递归了
        while srcQueue.__len__() > 0:
            trace = srcQueue.pop()
            # 当前匹配路径
            curSrcPath = os.path.join(srcPath, trace)
            curDestPath = os.path.join(destPath, trace)
            
            if lastSyncTime is not None:
                nearestTime = max([
                    os.path.getctime(curSrcPath),
                    os.path.getmtime(curSrcPath),
                ])
                if nearestTime <= lastSyncTime:
                    
                    print(FC.c("No Change: {}").format(curSrcPath))
                    continue

            print(FC.c("check: {}").format(curSrcPath))            

            if not os.path.isdir(curDestPath):
                os.mkdir(curDestPath)
            # 获得源,目标路径文件夹和文件
            srcFolders, srcFiles = self._getSubfolderAndFiles(curSrcPath)
            destFolders, destFiles = self._getSubfolderAndFiles(curDestPath)
            # 删除目标路径不存在文件(夹)
            destFolders = self._cleanOnlyExistInDest(srcFolders, destFolders, curDestPath)
            destFiles = self._cleanOnlyExistInDest(srcFiles, destFiles, curDestPath)
            # 比对更新文件
            self._syncFiles(curSrcPath, srcFiles, curDestPath, destFiles, lastSyncTime)
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

    def _checkBeforeDeleteFormerPath(self, path):
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

    def sync(self): 
        for fr in self.folderRefernece:
            self.updatedFolderRenference.append(fr[:2] + [self._getStrfTime()])
            
            print(FC.w("正在同步 {}", 'm').format(fr[0]))
            self._handleFolder(fr, trace='')
        
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
                    self.updatedFolderRenference.append(fr[:2] + [self._getStrfTime(fr[2])])
            self._updateFolderReference()
            print("删除完毕")
            self._checkBeforeDeleteFormerPath(srcPath)
            self._checkBeforeDeleteFormerPath(destPath)
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

                if srcPath != formerSrcPath:
                    assert not self._checkSameInReference(srcPath, 'src'), "路径已存在在当前备份中" 
                else:
                    print("文件夹未变动")
                    return           
                
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
                else:
                    print("文件夹未变动")
                    return    

            for fr in self.folderRefernece:
                if fr[2] is None:
                    self.updatedFolderRenference.append(fr[:2])
                else:
                    self.updatedFolderRenference.append(fr[:2] + [self._getStrfTime(fr[2])])
            self.updatedFolderRenference[_idx] = [srcPath, destPath]
            self._updateFolderReference()
            print("更新完毕")
            self._checkBeforeDeleteFormerPath( (formerSrcPath, formerDestPath)[modifyField - 1] )
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
                        str(idx).zfill(2), ref[0], ref[1], self._getStrfTime(ref[2]) ))


if __name__ == "__main__":
    buu = BackUpUtil()
    # buu.sync()
    buu.delRenference()