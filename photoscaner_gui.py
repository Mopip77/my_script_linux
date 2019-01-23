import tkinter as tk
import tkinter.font as tkFont
import pyautogui as pag
import os

from photoscaner import PhotoScaner


class PSWin(PhotoScaner):
    """
    PhotoScaner Window 候选提示窗
    """

    def __init__(self, filepath):
        # mouse position
        self.m_x, self.m_y = pag.position()
        self.window = tk.Tk()
        self.window.title('PhotoScaner')
        self.window.geometry('150x231+{}+{}'.format(self.m_x, self.m_y))
        self.ft15 = tkFont.Font(family='fangsong ti', size=15)
        self.ft12 = tkFont.Font(family='fangsong ti', size=12)
        self.ft12b = tkFont.Font(family='fangsong ti', size=15)
        super(PSWin, self).__init__(filepath)

    def __update_window_after_click(self, msg):
        self.lb1.pack_forget()
        self.b1.pack_forget()
        self.b2.pack_forget()
        self.b3.pack_forget()
        self.text = tk.Text(self.window, font=self.ft15)
        self.text.pack()
        self.text.insert(tk.INSERT, msg)

    def call_img_ocr(self):
        msg = self.img_ocr()
        self.__update_window_after_click(msg)

    def call_img_to_base64(self):
        msg = self.img_to_base64()
        self.__update_window_after_click(msg)

    def call_upload_to_img_bank(self):
        msg = self.upload_to_img_bank()
        msg = msg['data']
        self.window.geometry('650x300+{}+{}'.format(self.m_x, self.m_y))
        self.__update_window_after_click(msg)

    def run(self):
        self.lb1 = tk.Label(
            self.window,
            text='使用剪贴板的图片， \n结果保存到剪贴板 ',
            font=self.ft12,
            bg='yellow',
            height=2,
        )

        self.b1 = tk.Button(
            self.window,
            text='OCR',
            font=self.ft12b,
            width=20,
            height=2,
            command=self.call_img_ocr)

        self.b2 = tk.Button(
            self.window,
            text='base64',
            font=self.ft12b,
            width=20,
            height=2,
            command=self.call_img_to_base64)

        self.b3 = tk.Button(
            self.window,
            text='图床',
            font=self.ft12b,
            width=20,
            height=2,
            command=self.call_upload_to_img_bank)

        self.lb1.pack()
        self.b1.pack()
        self.b2.pack()
        self.b3.pack()

        self.window.mainloop()


if __name__ == "__main__":
    w = PSWin('/home/mopip77/Pictures/ScreenShot_2018-11-28_22:02:41.png')
    w.run()
