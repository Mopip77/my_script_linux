import time


def getStrfTime(pattern, t=None):
        """返回格式为pattern的时间字符串"""
        if t is None:
            return time.strftime(pattern, time.localtime())
        else:
            t = time.localtime(t)
            return time.strftime(pattern, t)