import random

def calc_center(top_left, bottom_right, offset=(0,0), factor=5):
    factor = 5
    h = random.randint(-factor, factor)
    v = random.randint(-factor, factor)
    point = (
        (top_left[0] + bottom_right[0]) // 2 + h + offset[0],
        (top_left[1] + bottom_right[1]) // 2 + v + offset[1]
    )

    return point

def source_name(source, mime):
    suffix = 'raw' if mime == 'raw' else 'png' if source == 'adb' else 'jpg'
    return f'{source}.{suffix}'
