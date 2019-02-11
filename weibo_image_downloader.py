import tkinter as tk
import time
import requests
import json
import os
import multiprocessing as mp
import re

from threading import Thread
from urllib.parse import urlencode
from tkinter import messagebox

cookies = {
    'SINAGLOBAL': '7212577498645.592.1546592349101',
    'wvr': '6',
    'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9Whi--i4kq7wWZan7kofmleQ5JpX5KMhUgL.FozE1KBpS0zXe0B2dJLoI7USdNWDMhMN',
    'UOR': ',,login.sina.com.cn',
    'ULV': '1549789569521:38:13:1:2480970622692.5444.1549789569466:1549670229635',
    'Ugrow-G0': '370f21725a3b0b57d0baaf8dd6f16a18',
    'YF-V5-G0': 'c99031715427fe982b79bf287ae448f6',
    'ALF': '1581420185',
    'SSOLoginState': '1549884188',
    'SCF': 'Ap-Qr7x5K6AOKeDGle8JJWEf7dJFlFJQEq2IFOjY4BCWjxOh0D5zkNkd7lYce9kFqDg3cpUdsnDJH0SzcT9yHMI.',
    'SUB': '_2A25xZStMDeRhGeRM4lYQ9yzIyDiIHXVSExuErDV8PUNbmtBeLUOnkW9NU9RZ22eOqE2v5hZN6I1oSkxX4uht_9cE',
    'SUHB': '04W_ZWnVA8ENcA',
}

headers = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
}

FILE_PATH = '/home/mopip77/Pictures'
ALBUMTYPE = ['全部图片', '面孔专辑']
IMAGETPYPE = ['small', 'large']

def get_userInfo(uid):
    url = 'https://weibo.com/{}'.format(uid)
    res = requests.get(url, cookies=cookies, allow_redirects=False)
    try:
        uid = re.findall('\'oid\']=\'(.*?)\'', res.text)[0]
        nickname = re.findall('\'onick\']=\'(.*?)\'', res.text)[0]
    except:
        try:
            url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value={}'.format(uid)
            res = requests.get(url, cookies=cookies, allow_redirects=False)
            doc = json.loads(res.text)
            nickname = doc['data']['userInfo']['screen_name']
        except:
            uid = ''
            nickname = ''
    return (uid, nickname)

def crawl_album(uid, albumType, page, image_type):
    if albumType == ALBUMTYPE[0]:
        type = 3
    else:
        type = 45

    url = 'http://photo.weibo.com/photos/get_all?uid={}&type={}&page={}'.format(uid, type, page)
    print(url)
    res = requests.get(url, cookies=cookies)
    doc = json.loads(res.text)
    l = []
    if doc['data']['photo_list']:
        for pic in doc['data']['photo_list']:
            create_time = pic['created_at']
            img_url = '{}/{}/{}'.format(pic['pic_host'], image_type, pic['pic_name'])
            photo_id = pic['photo_id']
            l.append((create_time, img_url, photo_id))
    print(len(l))
    return l

def format_data(img_data):
    """
    返回格式化日期 2019-01-01, 微博有三种(久远一点是格式化的日期, 今年的是1月3日, 最近是刚刚,5分钟前,今天)
    """
    if '-' in img_data:
        return img_data
    elif '月' in img_data:
        month, day = re.findall('(.*?)月(.*?)日', img_data)[0]
        year = time.localtime()[0]
        return '{}-{}-{}'.format(year, month, day)
    else:
        today = time.localtime()
        return '{}-{}-{}'.format(str(today[0]), str(today[1]), str(today[2]))


def save_img(img_data, img_url, img_id, fp):
    fileName = format_data(img_data)
    photoType = img_url.split('.')[-1]
    file_path = fp + fileName + '-' + img_id + '.' + photoType

    if not os.path.exists(file_path):
        res = requests.get(img_url, stream=True)
        with open(file_path, 'wb') as f:
            for chunk in res.iter_content(chunk_size=128):
                f.write(chunk)

    return True

def spider(uid, albumType, imageType, Weibo):
    t = time.time()
    nickname = Weibo.userInfo[1]
    fp = FILE_PATH + '/' + nickname + '/'
    if not os.path.exists(fp):
        os.mkdir(fp)
    fp = fp + albumType + imageType + '/'
    if not os.path.exists(fp):
        os.mkdir(fp)

    pool = mp.Pool(4)

    is_parsing = 1
    count = 1
    img_count = 0
    inc_count = 10

    while is_parsing:
        Weibo.upload('start crawling...')
        crawl_tasks = [pool.apply_async(crawl_album, args=(uid, albumType, page, imageType,)) for page in range(count, count + inc_count)]
        imgs = [j.get() for j in crawl_tasks]


        for img in imgs:
            if not img:
                is_parsing = 0
            else:
                img_savers = [pool.apply_async(save_img, args=(i[0], i[1], i[2], fp,)) for i in img]
                check_status = [j.get() for j in img_savers]
                img_count += len(img)
                Weibo.upload('has download {} imgs'.format(img_count))

        if is_parsing == 1:
            count += inc_count
    #该图库下没有图片
    if not img_count:
        return False
    Weibo.upload('parsing finished...')
    Weibo.upload('has downloaded {} images...'.format(img_count))
    Weibo.upload('use %.2f s...' % (time.time() - t))
    return True



class WeiboImage(object):

    def __init__(self):
        self.window = tk.Tk()
        self.window.title('微博图片下载器')
        self.window.geometry('450x200+400+400')

        self.lb = tk.Label(self.window, text='用户ID:', font=("Noto Mono", 18), height=4)
        self.lb.grid()

        self.ipt = tk.Entry(self.window, font=("Noto Mono", 18), width=20)
        self.ipt.grid(row=0, column=1, columnspan=2)

        self.album_type = tk.IntVar()
        self.album_type.set(0)
        self.chs = tk.Radiobutton(self.window, text=ALBUMTYPE[0], font=("Noto Mono", 15), variable=self.album_type, value=0)
        self.chs.grid(row=1, column=0)

        self.chs2 = tk.Radiobutton(self.window, text=ALBUMTYPE[1], font=("Noto Mono", 15), variable=self.album_type, value=1)
        self.chs2.grid(row=1, column=1)

        self.but = tk.Button(self.window, text='下载', height=2, width=8, font=("Noto Mono", 13), command=self.check_id)
        self.but.grid(row=1, column=2)

        self.run()

    def check_id(self):
        _id = self.ipt.get()

        self.userInfo = get_userInfo(_id)
        if not self.userInfo[0]:
            self.showInfo('没有该用户,请重新输入')
        else:
            print(self.userInfo)
            self.top = tk.Toplevel()
            self.top.title('下载确认')
            self.top.geometry('450x200+400+400')
            text = "确认要下载用户'{}'的{}吗?".format(self.userInfo[1], ALBUMTYPE[self.album_type.get()])
            lb = tk.Label(self.top, text=text, font=("Noto Mono", 16), height=4)
            lb.grid(row=0, columnspan=3, sticky=tk.E+tk.W)

            self.image_type = tk.IntVar()
            self.image_type.set(0)
            chs1 = tk.Radiobutton(self.top, text='small', font=("Noto Mono", 15), variable=self.image_type,value=0)
            chs1.grid(row=1, column=0)
            chs3 = tk.Radiobutton(self.top, text='large', font=("Noto Mono", 15), variable=self.image_type, value=1)
            chs3.grid(row=1, column=1)

            but = tk.Button(self.top, text="确认下载", font=("Noto Mono", 12), command=self.download, height=2)
            but.grid(row=2, columnspan=2)


    def download(self):
        self.top.destroy()
        self.text = tk.Listbox(self.window, height=15, width=37, font=("Noto Mono", 15))
        self.text.grid(row=2, column=0, columnspan=3)
        self.window.geometry('450x550+420+420')
        has_img = spider(self.userInfo[0], ALBUMTYPE[self.album_type.get()], IMAGETPYPE[self.image_type.get()], self)
        if not has_img:
            self.text.destroy()
            self.showInfo('该图库下没有图片!')


    def upload(self, value):
        if self.text.get(14):
            self.text.delete(0)
        self.text.insert(tk.END, value)
        self.window.update()


    def showInfo(self, message):
        tk.messagebox.showinfo(title='出错', message=message)

    def run(self):
        self.window.mainloop()



if __name__ == '__main__':
    weibo = WeiboImage()
