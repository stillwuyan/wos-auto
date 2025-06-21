import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
import subprocess
import random
import argparse
import pathlib
import time
import struct

template_set = {
    'heal': {
        'file': {
            'small': 'template/heal_small.png',
            'large': 'template/heal_large.png'
        },
        'area': {
            'small': None,
            'large': (780, 1900, 900, 2200)
        },
    },
    'heal_btn': {
        'file': {
            'small': 'template/en_heal_btn_small.png',
            'large': 'template/en_heal_btn_large.png'
        },
        'area': {
            'small': None,
            'large': (620, 1700, 1000, 1950)
        }
    },
    'heal_btn2': {
        'file': {
            'small': 'template/en_heal_btn2_small.png',
            'large': 'template/en_heal_btn2_large.png'
        },
        'area': {
            'small': None,
            'large': (620, 1700, 1000, 2000),
        }
    },
    'heal_btn3': {
        'file': {
            'small': 'template/en_heal_btn3_small.png',
            'large': 'template/en_heal_btn3_large.png'
        },
        'area': {
            'small': None,
            'large': (620, 1700, 1000, 2000),
        }
    },
    'help': {
        'file': {
            'small': 'template/help_small.png',
            'large': 'template/help_large.png'
        },
        'area': {
            'small': None,
            'large': (740, 2000, 900, 2300)
        }
    },
    'chat': {
        'file': {
            'small': 'template/chat_large.png',
            'large': 'template/chat_large.png'
        },
        'area': {
            'small': None,
            'large': (0, 50, 300, 200)
        }
    }
}

def calc_center(top_left, bottom_right):
    offset = 5
    h = random.randint(-offset, offset)
    v = random.randint(-offset, offset)
    point = ((top_left[0]+bottom_right[0])//2 + h, (top_left[1]+bottom_right[1])//2 + v)
    return point 

def read_png(img_file):
    return cv.imread(img_file, 0)

def draw_img(res, img, top_left, bottom_right):
    img_draw = img.copy()
    cv.rectangle(img_draw, top_left, bottom_right, (0, 0, 255), 4)

    point = calc_center(top_left, bottom_right)
    print(f'dot: {point}')
    cv.circle(img_draw, point, 5, (0, 255, 0), 4)

    plt.subplot(121),plt.imshow(res, cmap = 'gray')
    plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122),plt.imshow(img_draw, cmap = 'gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.show()
    return point

def do_match(img, tpl_file, area = None, debug = False):
    if debug:
        start = time.perf_counter()

    template = cv.imread(tpl_file, 0)

    methods = ['cv.TM_CCOEFF', 'cv.TM_CCOEFF_NORMED', 'cv.TM_CCORR',
               'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED']
    method = eval(methods[1])

    if area:
        x, y, w, h = area
        area_img = img[y:y+h, x:x+w]
    else:
        x, y, w, h = (0, 0, 1080, 2400) 
        area_img = img

    # Apply template Matching
    res = cv.matchTemplate(area_img, template, method)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    bottom_right = (top_left[0] + template.shape[1], top_left[1] + template.shape[0])

    # Convert to global
    top_left = (top_left[0] + x, top_left[1] + y)
    bottom_right = (bottom_right[0] + x, bottom_right[1] + y)

    if debug:
        end = time.perf_counter()
        print(img.shape)
        print(f"match time: {end - start:.6f}s")
        print(f'img: {img.shape[::-1]}')
        print(f'pos: {*top_left, *bottom_right}')
        print(f'con: {max_val:.2f}')
        point = draw_img(res, img, top_left, bottom_right)
    else:
        point = calc_center(top_left, bottom_right)
    return point, max_val

def do_capture(debug=False):
    if debug:
        start = time.perf_counter()

    pathlib.Path('./output').mkdir(parents=True, exist_ok=True)
    output = './output/capture.png'
    command = ['adb', 'exec-out', 'screencap', '-p']
    with open(output, 'wb') as f:
        process = subprocess.run(command, stdout=f)

    if debug:
        end = time.perf_counter()
        print(f"capture time: {end - start:.6f}s")
    return read_png(output)

def do_capture_raw(debug=False):
    if debug:
        start = time.perf_counter()

    command = ['adb', 'exec-out', 'screencap']
    process = subprocess.run(command, stdout=subprocess.PIPE)
    raw_data = process.stdout

    if debug:
        end = time.perf_counter()
        print(f"capture time: {end - start:.6f}s")

    if len(raw_data) > 16:
        header = raw_data[:16]
        width, height, pixel_format, reserved = struct.unpack('<IIII', header)
        offset = len(raw_data) - (width * height * 4)
        data = raw_data[offset:]
    else:
        print('capture failed')
        data = raw_data
        pixel_format = 0

    format_mapping = {
        1: 'RGBA_8888',
        2: 'RGBX_8888',
        3: 'RGB_888',
        4: 'RGB_565',
        0: 'unknown'
    }
    if format_mapping[pixel_format] == 'RGBA_8888':
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 4))
        img = cv.cvtColor(arr, cv.COLOR_RGBA2GRAY)
    elif format_mapping[pixel_format] == 'RGBX_8888':
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 4))
        img = cv.cvtColor(arr[:, :, :3], cv.COLOR_RGB2GRAY)
    elif format_mapping[pixel_format] == 'RGB_888':
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
        img = cv.cvtColor(arr, cv.COLOR_RGB2GRAY)
    elif format_mapping[pixel_format] == 'RGB_565':
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width))
        img = cv.cvtColor(arr, cv.COLOR_BGR5652GRAY)
    else:
        img = None

    return img

def do_click(pos, debug=False):
    command = ['adb', 'shell', 'input', 'tap', str(pos[0]), str(pos[1])]
    if debug:
        print(f'cmd: {" ".join(command)}')
    subprocess.run(command)

def do_chat(img, size):
    offset = 50
    tpl = template_set['chat']['file'][size]
    area = template_set['chat']['area'][size]
    pos, con = do_match(img, tpl, area)
    pos = (pos[0] - offset, pos[1])
    if con > 0.7:
        do_click(pos)

def do_heal(img, size):
    tpl = template_set['heal_btn3']['file'][size]
    area = template_set['heal_btn3']['area'][size]
    pos, con = do_match(img, tpl, area)

    if con > 0.8:
        print(f"😀 Do hea3 {con:.2f} : {pos}")
        return

    tpl = template_set['heal_btn2']['file'][size]
    area = template_set['heal_btn2']['area'][size]
    pos, con = do_match(img, tpl, area)

    if con > 0.8:
        print(f"😀 Do hea2 {con:.2f} : {pos}")
        do_click(pos)
        return

    offset = 10
    tpl = template_set['heal_btn']['file'][size]
    area = template_set['heal_btn']['area'][size]
    pos, con = do_match(img, tpl, area)
    pos = (pos[0], pos[1] + offset)

    if con > 0.8:
        print(f"😀 Do hea1 {con:.2f} : {pos}")
        do_click(pos)
        return

    tpl = template_set['heal']['file'][size]
    area = template_set['heal']['area'][size]
    pos, con = do_match(img, tpl, area)

    if con > 0.7:
        print(f"😀 Do heal {con:.2f} : {pos}")
        do_click(pos)
    else:
        print(f"😢 No heal {con:.2f} : {pos}")

def do_help(img, size):
    tpl = template_set['help']['file'][size]
    area = template_set['help']['area'][size]
    pos, con = do_match(img, tpl, area)

    if con > 0.8:
        print(f"😀 Do help {con:.2f} : {pos}")
        do_click(pos)
    else:
        print(f"😢 No help {con:.2f} : {pos}")

def test(size, format):
    spliter = lambda name : '*'*10 + name + '*'*10
    if format == 'raw':
        print(spliter('capture raw'))
        img = do_capture_raw(True)
    else:
        print(spliter('capture png'))
        img = do_capture(True)

    print(spliter('check heal'))
    tpl_file = template_set['heal']['file'][size]
    tpl_area = template_set['heal']['area'][size]
    do_match(img, tpl_file, tpl_area, True)

    print(spliter('check help'))
    tpl_file = template_set['help']['file'][size]
    tpl_area = template_set['help']['area'][size]
    do_match(img, tpl_file, tpl_area, True)

    print(spliter('check chat'))
    tpl_file = template_set['chat']['file'][size]
    tpl_area = template_set['chat']['area'][size]
    do_match(img, tpl_file, tpl_area, True)

    print(spliter('check heal btn1'))
    tpl_file = template_set['heal_btn']['file'][size]
    tpl_area = template_set['heal_btn']['area'][size]
    do_match(img, tpl_file, tpl_area, True)

    print(spliter('check heal btn2'))
    tpl_file = template_set['heal_btn2']['file'][size]
    tpl_area = template_set['heal_btn2']['area'][size]
    do_match(img, tpl_file, tpl_area, True)

    print(spliter('check heal btn3'))
    tpl_file = template_set['heal_btn3']['file'][size]
    tpl_area = template_set['heal_btn3']['area'][size]
    do_match(img, tpl_file, tpl_area, True)

def main(interval, size, format):
    try:
        while True:
            img = do_capture_raw() if format == 'raw' else do_capture()
            do_help(img, size)
            do_heal(img, size)
            do_chat(img, size)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser('python main.py')
    parser.add_argument('-t', '--test', action='store_true', help='Test command')
    parser.add_argument('-i', '--interval', type=float, default=1.0, help='Set cycle interval (seconds)')
    parser.add_argument('-s', '--size', type=str, default='large', choices=['small', 'large'], help='Choose template size')
    parser.add_argument('-f', '--format', type=str, default='raw', choices=['raw', 'png'], help='Choose image format')

    args = parser.parse_args()
    if args.test:
        test(args.size, args.format)
    else:
        main(args.interval, args.size, args.format)