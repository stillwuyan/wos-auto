import pathlib
import adb
import net
import template
import image

def spliter(msg):
    msg_len = len(msg.strip())
    total_len = 50
    half_len = (total_len - msg_len) // 2
    content = f"{'*'*half_len}{msg}{'*'*half_len}"
    if len(content) < total_len:
        content += '*'*(total_len-len(content))
    print(content)

def capture(source):
    spliter(f'capture {source}')
    output_dir = '../output'
    output = f'{output_dir}/capture.{source}'
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    match source:
        case 'adb.raw':
            img = adb.read_raw()
            image.save_raw(output, img)
        case 'adb.png':
            img = adb.read_png()
            image.save_img(output, img)
        case 'net.raw':
            g = net.read_raw()
            img = next(g)
            image.save_raw(output, img)
        case 'net.jpg':
            g = net.read_jpg()
            img = next(g)
            image.save_img(output, img)
        case _:
            print(f'unknown source: {source}')
    return output

def display(file, source):
    if 'raw' in source:
        img = image.load_raw(file)
    else:
        img = image.load_img(file)
    image.show(img)

def chat(file, source, target):
    spliter('check chat')
    tpl_file = template.config[target]['chat']['file']
    tpl_area = template.config[target]['chat']['area']

    if 'raw' in source:
        img = image.load_raw(file)
    else:
        img = image.load_img(file)
    image.match_tpl(img, tpl_file, area=tpl_area, debug=True)

def help(file, source, target):
    spliter('check help')
    tpl_file = template.config[target]['help']['file']
    tpl_area = template.config[target]['help']['area']

    if 'raw' in source:
        img = image.load_raw(file)
    else:
        img = image.load_img(file)
    image.match_tpl(img, tpl_file, area=tpl_area, debug=True)

def heal(file, source, target):
    if 'raw' in source:
        img = image.load_raw(file)
    else:
        img = image.load_img(file)

    spliter('check heal')
    tpl_file = template.config[target]['heal']['file']
    tpl_area = template.config[target]['heal']['area']
    image.match_tpl(img, tpl_file, area=tpl_area, debug=True)

    spliter('check heal btn1')
    tpl_file = template.config[target]['heal_s2']['file']
    tpl_area = template.config[target]['heal_s2']['area']
    image.match_tpl(img, tpl_file, area=tpl_area, debug=True)

    spliter('check heal btn2')
    tpl_file = template.config[target]['heal_s3']['file']
    tpl_area = template.config[target]['heal_s3']['area']
    image.match_tpl(img, tpl_file, area=tpl_area, debug=True)

    spliter('check heal btn3')
    tpl_file = template.config[target]['heal_s4']['file']
    tpl_area = template.config[target]['heal_s4']['area']
    image.match_tpl(img, tpl_file, area=tpl_area, debug=True)

def all(source, target):
    file = capture(source)
    chat(file, source, target)
    help(file, source, target)
    heal(file, source, target)

def conv(file):
    if 'raw' not in file:
        print('input file must be raw file')
        return

    output_dir = '../output'
    output = f'{output_dir}/output.png'
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    img = image.load_raw(file)
    image.save_img(output, img)