#!/usr/bin/env python3
import os
import sys

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


def getSpecificFileExtensionFiles(files, extensions):
    extensionFiles = []
    for f in files:
        if f.split('.')[-1] in extensions:
            print("[found] " + f)
            extensionFiles.append(f)
        
    return extensionFiles


def handleFolder(rootPath, extensions=['html', 'py'], trace='', level=0):
    printStack = []

    # 当前匹配路径
    curPath = os.path.join(rootPath, trace)
    
    # 文件夹内部文件改变,文件夹的修改时间并不会变,所以以此判断可能会造成漏判
    print("check: {}".format(curPath))            

    # 获得源,目标路径文件夹和文件
    folders, files = getSubfolderAndFiles(curPath)
    folders = [handleFolder(rootPath, trace=os.path.join(trace, f), level=level + 1) for f in folders]
    files = getSpecificFileExtensionFiles(files, extensions)
    if len(files):
        files.sort()

    printStack += [[f, level + 1] for f in files]
    for f in folders:
        if f == []:
            continue
        printStack += f
    
    if len(printStack):
        printStack.insert(0, [trace.split('/')[-1], level, 1])
    
    return printStack


def tabPrint(item):
    tab = '  '

    path, level = item[:2]
    isFolder = False
    if len(item) > 2:
        isFolder = True
    
    if isFolder is True:
        print("\033[0;32m" + tab * level + path + "\033[0m")
    else:
        print(tab * level + path)


############################################################

def htmlRender(treeFolder, folderName):
    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>%s</title>
    <style>
        a {
            text-decoration: none;
            font-size: 14px;
            color: black;
        }
        div {
            line-height: 20px;
            position: relative;
            left: 12px;
        }
        .folder {
            font-size: 15px;
            font-weight: bold;
            color: green;
        }
        li {
            font-size: 14px;
            list-style-type: none;
        }
    </style>
</head>
<body>
    %s
</body>
</html>"""

    appendHtml = ""
    levelStack = []
    levelStack.append(treeFolder.pop(0))
    while len(treeFolder):
        curItem = treeFolder.pop(0)
        levelInc = curItem[1] - levelStack[-1][1]

        if levelInc > 0:
            # 进入(补充div)子文件夹只能进入一层
            appendHtml += "<div>"
        else:
            # 退出能退出多层(补充</div>)
            appendHtml += "</div>" * (0 - levelInc)

        levelStack = levelStack[:curItem[1]]
        levelStack.append(curItem)

        if len(curItem) > 2:
            appendHtml += folderHtml(curItem[0])
        else:
            # 第一个是根目录名称,是空字符串
            link = '/'.join([level[0] for level in levelStack[1:]])
            appendHtml += fileHtml(curItem[0], link)
        
    
    # 最后补充未补全的</div>
    appendHtml += "</div>" * len(levelStack)
    return template % (folderName, appendHtml)

def folderHtml(text):
    return '<li class="folder">{}</li>'.format(text)

def fileHtml(text, link):
    return '<li><a href="{}">{}</a></li>'.format(link, text)

def saveAsIndex(html, folderPath):
    with open(folderPath + '/index.html', 'w') as f:
        f.write(html)
    print("索引文件保存为: " + folderPath + '/index.html')

if __name__ == "__main__":
    # "/home/mopip77/Documents/notebook/ML
    targetPath = os.path.realpath(sys.argv[1])
    a = handleFolder(os.path.realpath(targetPath))
    saveAsIndex(htmlRender(a, targetPath), targetPath)
