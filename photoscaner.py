import json
import sys
import requests
import pyperclip
import os


class PhotoScaner(object):
    """
    将图片OCR, 转base64, 上传到图床
    """

    # smms, qiniu
    DAFAULT_PICHOST = 'smms'

    def __init__(self, filepath):
        self.filePath = filepath
        self.fileName = self.filePath.split('/')[-1]
        self.img = self.__get_file_content(filepath)
        self.mdData = {
            'host': '',
            'url': ''
        }

    def __call__(self, sign):
            if sign == 'smms':
                return self.upload_to_SMMS()
            elif sign == 'qiniu':
                return self.upload_to_QINIU()

    def __get_file_content(self, filepath):
        with open(filepath, 'rb') as f:
            return f.read()

    def img_ocr(self, linefeed=False):
        from my_info import BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY
        from aip import AipOcr
        
        client = AipOcr(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)

        result = client.basicGeneral(self.img)
        text_line = [line['words'] for line in result['words_result']]
        if linefeed is True:
            res = '\n'.join(text_line)
        else:
            res = ''.join(text_line)
        msg = "OCR result:\n{}\n".format(res)
        self.set_clipboard(res)
        return msg

    def img_to_base64(self):
        import base64

        bs = base64.b64encode(self.img).decode('utf-8')
        self.set_clipboard(bs)
        displayBs = bs[0:20] + "//////////////////////////" + bs[-20:-1]
        msg = "base64 result:\n{}\n".format(displayBs)
        return msg

    def upload_to_img_bank(self):
        # 测试发现传小文件多线程优势不明显
        # 大文件多线程反而慢,并且多线程无法同步类成员变量,弃用
        # import multiprocessing
        
        # res = {}
        # pool = multiprocessing.Pool(2)

        # t1 = pool.apply_async(self, args=('smms',))
        # t2 = pool.apply_async(self, args=('qiniu',))
        # pool.close()
        # pool.join()
        # res['smms'] = t1.get()
        # res['qiniu'] = t2.get()
        # print(self.mdUrl)
        import time
        from pymongo import MongoClient
        from my_info import DB_PWD, DB_SERVER, DB_USER, DB_PORT

        database = 'pichosting'
        client = MongoClient('mongodb://{}:{}@{}:{}/{}'.format(
            DB_USER,
            DB_PWD,
            DB_SERVER,
            DB_PORT,
            database
        ))
        db = client[database]

        res = {}
        res['smms'] = self.upload_to_SMMS()
        res['qiniu'] = self.upload_to_QINIU()

        if self.mdData['url'] != '':
            self.set_clipboard(self.mdData['url'])

        ret_msg = ''
        database_item = {
            'name': self.fileName,
            'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        for host in res.keys():
            if host == self.DAFAULT_PICHOST:
                ret_msg += '{}{}:\n{}\n'.format(host, '(default)', res[host]['data'])
            else:
                ret_msg += '{}:\n{}\n'.format(host, res[host]['data'])
            if 'url' in res[host].keys():
                database_item[host] = res[host]['url']

        if db['photoscaner'].insert_one(database_item):
            ret_msg += "上传数据库成功...\n"
        else:
            ret_msg += "上传数据库失败...\n"
        return ret_msg

    def rend_upload_return(self, status, data, method):
        """
        渲染上传返回,status为上传状态,data在成功上传时为url,失败为error_msg
        method 是哪个图床,如果为默认图床则复制到剪贴板
        """
        reply_data = {}
        if status:
            md = "![{}]({})".format(self.fileName, data)
            if self.mdData['url'] == '':
                self.mdData['url'] = md
                self.mdData['host'] = method
            if method == self.DAFAULT_PICHOST:
                self.mdData['url'] = md
                self.mdData['host'] = method
            reply_data['status'] = 'ok'
            reply_data['data'] = "url:  {}\nmd :  {}\n".format(data, md)
            reply_data['url'] = data
        else:
            reply_data['status'] = 'error'
            reply_data['data'] = "Photo is FAIL to upload...\n" +\
                                 "Failure type:{}\n".format(data)
        return reply_data

    def upload_to_SMMS(self):
        # sm.ms
        # upload
        url = 'https://sm.ms/api/upload'

        # 好像全路径或中文的上传会失败，只保留编码后文件名上传
        from urllib.parse import quote
        fileName = quote(self.fileName)
        files = {
            "smfile": (fileName, self.img, "image/jpeg"),
        }

        res = requests.post(url, files=files)
        doc = json.loads(res.text)

        # parse response
        if doc['code'] == 'error':
            reply_data = self.rend_upload_return(False, doc['msg'], 'smms')
        else:
            reply_data = self.rend_upload_return(True, doc['data']['url'], 'smms')
        return reply_data

    def upload_to_QINIU(self):
        from qiniu import Auth, put_file, etag
        import qiniu.config
        import time
        from my_info import QINIU_KEY, QINIU_SECRET, QINIU_BUCKET, QINIU_DEFAULT_DOMAIN

        try:
            access_key = QINIU_KEY
            secret_key = QINIU_SECRET
            #构建鉴权对象
            q = Auth(access_key, secret_key)
            #要上传的空间
            bucket_name = QINIU_BUCKET
            #上传到七牛后保存的文件名
            year, month, day = time.localtime()[0:3]
            key = '{}_{}_{}_{}'.format(year, month, day, self.fileName)
            #生成上传 Token，可以指定过期时间等
            token = q.upload_token(bucket_name, key, 3600)
            #要上传文件的本地路径
            localfile = self.filePath
            ret, info = put_file(token, key, localfile)
            assert ret['key'] == key
            assert ret['hash'] == etag(localfile)

            pic_link = QINIU_DEFAULT_DOMAIN + key
            reply_data = self.rend_upload_return(True, pic_link, 'qiniu')
        except Exception as e:
            reply_data = self.rend_upload_return(False, e, 'qiniu')
        finally:
            return reply_data

    def image_search(self):
        """
        百度和google搜图，由于分别上传代码有难度且浪费重复时间
        所以先上传到图床再搜索，使用smms，这里就不重构了
        并且google会重定向，百度则需要提取一下url
        """
        url = 'https://sm.ms/api/upload'

        # 好像全路径或中文的上传会失败，只保留编码后文件名上传
        from urllib.parse import quote
        fileName = quote(self.fileName)
        files = {
            "smfile": (fileName, self.img, "image/jpeg"),
        }

        res = requests.post(url, files=files)
        doc = json.loads(res.text)

        # parse response
        if doc['code'] == 'error':
            print('搜图失败...\n' + doc['msg'])
        else:
            img_url = doc['data']['url']
            goo_url = 'https://www.google.com/searchbyimage?image_url={}&btnG=%E6%8C%89%E5%9B%BE%E7%89%87%E6%90%9C%E7%B4%A2'.format(img_url)
            
            subprocess_options = ['google-chrome', goo_url]
            
            baidu_search_url = 'https://graph.baidu.com/upload?image={}'.format(img_url)
            r = requests.get(baidu_search_url)
            doc = json.loads(r.text)
            if doc['msg'] == "Success":
                baidu_url = 'https://graph.baidu.com/s?sign=' + doc['data']['sign'] + '&tpl_from=pc'
                subprocess_options.append(baidu_url)

            # 直接用chrome打开
            import subprocess
            subprocess.call(subprocess_options)

    # 设置剪贴板
    def set_clipboard(self, sourceStr):
        self.clipboardHasSet = True
        pyperclip.copy(sourceStr)


def main():
    instruction="""
usage: pho <method> [option] <path>

<method>:
  o [LF]     image ocr (using LF: return the result with linefeed)
  b          image to base64
  u          upload image to image bank('sm.ms' and 'qiniu')
  s          search image

if using pho without <path> the path will be replaced by the latest screenshot
"""

    try:
        # process args
        args = sys.argv
        fp = args.pop()
        method = args[1]
        option = args[2:]
        
        if not os.path.isfile(fp):
            print("该文件不存在,请输入正确的文件地址")
            return
    except:
        print("命令格式不正确, 请用pho -h查看使用说明")
        return
    

    try:
        ps = PhotoScaner(fp)

        if method == 'o':
            print(ps.img_ocr(linefeed='-lf' in option))
            print('ocr result has sebt to clipboard...')

        elif method == 'b':
            print(ps.img_to_base64())
            print('base64 code has sent to clipboard...')

        elif method == 'u':
            rep = ps.upload_to_img_bank()
            print(rep)
            # 所有图床失效,未复制到剪贴板
            if ps.mdData['url'] == '':
                print('完蛋,所有图床失效')
            else:
                print('({})md link has sent to clipboard...'.format(ps.mdData['host']))

        elif method == 's':
            ps.image_search()
                
        elif method == '-h':
            print(instruction)
        else:
            print('use -h for help')
    except Exception as e:
        print('catch exception:{}'.format(e))


if __name__ == "__main__":
    main()
    # ps = PhotoScaner('/home/mopip77/Downloads/吉冈里帆.jpg')
    # ps.image_search()
