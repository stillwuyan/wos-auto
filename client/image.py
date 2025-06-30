from matplotlib import pyplot as plt
import cv2 as cv
import numpy as np
import time
import utils

def draw(ref, img, top_left, bottom_right, point):
    img_draw = img.copy()

    cv.rectangle(img_draw, top_left, bottom_right, (0, 0, 255), 4)
    cv.circle(img_draw, point, 5, (0, 255, 0), 4)

    plt.subplot(121),plt.imshow(ref, cmap = 'gray')
    plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122),plt.imshow(img_draw, cmap = 'gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.show()

def match_tpl(img, tpl, area=None, mid=1, offset=(0,0), debug=False):
    if debug:
        start = time.perf_counter()

    tpl_img = load_img(tpl)

    method_list = [
        'cv.TM_CCOEFF', 'cv.TM_CCOEFF_NORMED',
        'cv.TM_CCORR', 'cv.TM_CCORR_NORMED',
        'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED'
    ]
    method = eval(method_list[mid])

    if area:
        x, y, w, h = area
        area_img = img[y:y+h, x:x+w]
    else:
        x, y, w, h = 0, 0, img.shape[1], img.shape[0]
        area_img = img

    # Apply template Matching
    ref = cv.matchTemplate(area_img, tpl_img, method)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(ref)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    bottom_right = (top_left[0] + tpl_img.shape[1], top_left[1] + tpl_img.shape[0])

    # Convert to original image coordinate system
    top_left = (top_left[0] + x, top_left[1] + y)
    bottom_right = (bottom_right[0] + x, bottom_right[1] + y)

    point = utils.calc_center(top_left, bottom_right, offset=offset)
    if debug:
        end = time.perf_counter()
        print(f'match template: {end - start}')
        print(f'img: {img.shape}')
        print(f'pos: {*top_left, *bottom_right}')
        print(f'dot: {point}')
        print(f'con: {max_val:.2f}')
        draw(ref, img, top_left, bottom_right, point)

    return point, max_val

def load_img(file):
    return cv.imread(file, cv.IMREAD_GRAYSCALE)

def load_raw(file):
    with open(file, 'rb') as f:
        height = int.from_bytes(f.read(4), byteorder='little')
        width = int.from_bytes(f.read(4), byteorder='little')
        data = f.read()
    return parse_raw(data, 'GRAY', width, height)

def parse_img(data):
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv.imdecode(arr, cv.IMREAD_GRAYSCALE)

def parse_raw(data, fmt, width, height, padding=0):
    if fmt == 'RGBA_8888':
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 4))
        if padding > 0:
            arr = arr[:, :(width-padding), :]
        img = cv.cvtColor(arr, cv.COLOR_RGBA2GRAY)
    elif fmt == 'RGBX_8888':
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 4))
        img = cv.cvtColor(arr[:, :, :3], cv.COLOR_RGB2GRAY)
    elif fmt == 'RGB_888':
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
        img = cv.cvtColor(arr, cv.COLOR_RGB2GRAY)
    elif fmt == 'RGB_565':
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width))
        img = cv.cvtColor(arr, cv.COLOR_BGR5652GRAY)
    elif fmt == 'GRAY':
        img = np.frombuffer(data, dtype=np.uint8).reshape((height, width))
    else:
        print(f'invalid format {fmt}')
        img = None

    return img

def save_img(file, img):
    if img is None:
        print('empty image data')
        return

    cv.imwrite(file, img)

def save_raw(file, img):
    if img is None:
        print('empty image raw')
        return

    height, width = img.shape
    with open(file, 'wb') as f:
        f.write(height.to_bytes(4, byteorder='little'))
        f.write(width.to_bytes(4, byteorder='little'))
        f.write(img.tobytes())

def show(img):
    # Use BGRA inside
    while True:
        cv.imshow("img", img)
        cv.waitKey(1)

    cv.destroyAllWindows()