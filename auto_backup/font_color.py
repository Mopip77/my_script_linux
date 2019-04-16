###
# 用来返回带颜色的字体
# 

COLORS = [
    'bl', # black
    'r',  # red
    'g',  # green
    'y',  # yellow
    'b',  # blue
    'm',  # magenta
    'c',  # cyan
    'w',  # white
]

TEXT_FORMAT = "\033[{};3{}m{}\033[0m"
TEXT_FORMAT_WITH_BG = "\033[{};3{};4{}m{}\033[0m"

def _general_render(text, front_color, back_color, disp):
    if back_color is None:
        return TEXT_FORMAT.format(
            disp,
            COLORS.index(front_color),
            text)
    else:
        c = COLORS.index(back_color)
        if c >= 0:
            return TEXT_FORMAT_WITH_BG.format(
                disp,
                COLORS.index(front_color),
                COLORS.index(back_color),
                text)
        else:
            # 背景输入有误
            return TEXT_FORMAT.format(
                disp,
                COLORS.index(front_color),
                text)

def black(text, back_color=None, disp=0):
    return _general_render(text, 'bl', back_color, disp)

def bl(text, back_color=None, disp=0):
    return _general_render(text, 'bl', back_color, disp)

def red(text, back_color=None, disp=0):
    return _general_render(text, 'r', back_color, disp)

def r(text, back_color=None, disp=0):
    return _general_render(text, 'r', back_color, disp)

def green(text, back_color=None, disp=0):
    return _general_render(text, 'g', back_color, disp)

def g(text, back_color=None, disp=0):
    return _general_render(text, 'g', back_color, disp)

def yellow(text, back_color=None, disp=0):
    return _general_render(text, 'y', back_color, disp)

def y(text, back_color=None, disp=0):
    return _general_render(text, 'y', back_color, disp)

def blue(text, back_color=None, disp=0):
    return _general_render(text, 'b', back_color, disp)

def b(text, back_color=None, disp=0):
    return _general_render(text, 'b', back_color, disp)

def magenta(text, back_color=None, disp=0):
    return _general_render(text, 'b', back_color, disp)

def m(text, back_color=None, disp=0):
    return _general_render(text, 'b', back_color, disp)

def cyan(text, back_color=None, disp=0):
    return _general_render(text, 'c', back_color, disp)

def c(text, back_color=None, disp=0):
    return _general_render(text, 'c', back_color, disp)

def white(text, back_color=None, disp=0):
    return _general_render(text, 'w', back_color, disp)

def w(text, back_color=None, disp=0):
    return _general_render(text, 'w', back_color, disp)


if __name__ == "__main__":
    print(g("你好", 'r', 5))