import subprocess
import struct
import image

def read_png():
    command = ['adb', 'exec-out', 'screencap', '-p']
    process = subprocess.run(command, stdout=subprocess.PIPE)

    data = process.stdout
    return image.parse_img(data)

def read_raw():
    command = ['adb', 'exec-out', 'screencap']
    process = subprocess.run(command, stdout=subprocess.PIPE)
    data = process.stdout

    if len(data) > 16:
        header = data[:16]
        width, height, pixel_format, reserved = struct.unpack('<IIII', header)
        offset = len(data) - (width * height * 4)
        payload = data[offset:]
    else:
        print('invalid adb raw data')
        return None

    format_mapping = {
        1: 'RGBA_8888',
        2: 'RGBX_8888',
        3: 'RGB_888',
        4: 'RGB_565',
        0: 'unknown'
    }
    fmt = format_mapping[pixel_format]
    return image.parse_raw(payload, fmt, width, height)

def click(pos):
    command = ['adb', 'shell', 'input', 'tap', str(pos[0]), str(pos[1])]
    #print(f'cmd: {" ".join(command)}')
    subprocess.run(command)