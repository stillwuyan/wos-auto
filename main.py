import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
import subprocess
import random
import argparse
import pathlib
import time
import struct

def calc_center(top_left, bottom_right):
    offset = 10
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

def do_match(img, tpl_file, debug = False):
    if debug:
        start = time.perf_counter()

    template = cv.imread(tpl_file, 0)
    w, h = template.shape[::-1]

    methods = ['cv.TM_CCOEFF', 'cv.TM_CCOEFF_NORMED', 'cv.TM_CCORR',
               'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED']
    method = eval(methods[1])

    # Apply template Matching
    res = cv.matchTemplate(img, template, method)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)

    if debug:
        end = time.perf_counter()
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
        data = raw_data[16:]
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
    # print(f'cmd: {" ".join(command)}')
    subprocess.run(command)

def do_heal(img):
    template_file = 'template/heal.png'
    pos, con = do_match(img, template_file)

    if con > 0.7:
        print(f"😀 Do heal {con:.2f} : {pos}")
        do_click(pos)
        # Heal button
        time.sleep(0.6)
        pos = calc_center((634, 1821), (921, 1947))
        do_click(pos)
        # Help button
        time.sleep(0.6)
        pos = calc_center((634, 1821), (921, 1947))
        do_click(pos)
    else:
        print(f"😢 No heal {con:.2f} : {pos}")

def do_help(img):
    template_file = 'template/help.png'
    pos, con = do_match(img, template_file)

    if con > 0.8:
        print(f"😀 Do help {con:.2f} : {pos}")
        do_click(pos)
    else:
        print(f"😢 No help {con:.2f} : {pos}")

def test_heal():
    img_file = 'template/heal_screenshot.png'
    template_file = 'template/heal.png'
    do_match(read_png(img_file), template_file, True)

    img_file = 'template/heal_btn_screenshot.png'
    template_file = 'template/heal_btn.png'
    do_match(read_png(img_file), template_file, True)

def test_help():
    img_file = 'template/help_screenshot.png'
    template_file = 'template/help.png'
    do_match(read_png(img_file), template_file, True)

def test_capture():
    img = do_capture_raw(True)
    # img = do_capture(True)

    template_file = 'template/heal.png'
    do_match(img, template_file, True)

    template_file = 'template/help.png'
    do_match(img, template_file, True)

def main(interval):
    try:
        while True:
            img = do_capture_raw()
            do_help(img)
            do_heal(img)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser('python main.py')
    parser.add_argument('-t', '--test', type=str, choices=['heal', 'help', 'capture'], help='Test command')
    parser.add_argument('-i', '--interval', type=float, default=1.0, help='Set cycle interval (seconds)')

    args = parser.parse_args()
    match args.test:
        case 'heal':
            test_heal()
        case 'help':
            test_help()
        case 'capture':
            test_capture()
        case _:
            main(args.interval)