import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
import subprocess
import random
import pathlib
import time
import sys

def calc_center(top_left, bottom_right):
    offset = 10
    h = random.randint(-offset, offset)
    v = random.randint(-offset, offset)
    point = ((top_left[0]+bottom_right[0])//2 + h, (top_left[1]+bottom_right[1])//2 + v)
    return point 


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

def do_match(img_file, tpl_file, debug = False):
    if debug:
        start = time.perf_counter()

    img = cv.imread(img_file, 0)

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

def do_capture():
    pathlib.Path('./output').mkdir(parents=True, exist_ok=True)
    output = './output/capture.png'
    command = ['adb', 'exec-out', 'screencap', '-p']
    with open(output, 'wb') as f:
        process = subprocess.run(command, stdout=f)
    return output

def do_click(pos, debug = False):
    command = ['adb', 'shell', 'input', 'tap', str(pos[0]), str(pos[1])]
    # print(f'cmd: {" ".join(command)}')
    subprocess.run(command)

def do_heal(img_file):
    template_file = 'template/heal.png'
    pos, con = do_match(img_file, template_file)

    if con > 0.8:
        print(f"😀 Do heal {con:.2f} : {pos}")
        do_click(pos)
        # Heal button
        time.sleep(0.2)
        pos = calc_center((634, 1821), (921, 1947))
        do_click(pos)
        # Help button
        time.sleep(0.2)
        pos = calc_center((634, 1821), (921, 1947))
        do_click(pos)
    else:
        print(f"😢 No heal {con:.2f} : {pos}")

def do_help(img_file):
    template_file = 'template/help.png'
    pos, con = do_match(img_file, template_file)

    if con > 0.8:
        print(f"😀 Do help {con:.2f} : {pos}")
        do_click(pos)
    else:
        print(f"😢 No help {con:.2f} : {pos}")

def test_heal():
    img_file = 'template/heal_screenshot.png'
    template_file = 'template/heal.png'
    do_match(img_file, template_file, True)

    img_file = 'template/heal_btn_screenshot.png'
    template_file = 'template/heal_btn.png'
    do_match(img_file, template_file, True)

def test_help():
    img_file = 'template/help_screenshot.png'
    template_file = 'template/help.png'
    do_match(img_file, template_file, True)

def test_capture():
    img_file = do_capture()

    template_file = 'template/heal.png'
    do_match(img_file, template_file, True)

    template_file = 'template/help.png'
    do_match(img_file, template_file, True)

def main():
    try:
        while True:
            img_file = do_capture()
            do_help(img_file)
            do_heal(img_file)
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    if len(sys.argv) > 1:
        option = sys.argv[1]
    else:
        option = 'default'

    if option == 'heal':
        test_heal()
    elif option == 'help':
        test_help()
    elif option == 'capture':
        test_capture()
    else:
        main() 
