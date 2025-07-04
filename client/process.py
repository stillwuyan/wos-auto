from enum import Enum
import time

import template
import image
import net
import adb

class State(Enum):
    IDLE = 0
    HEAL_STEP1 = 1
    HEAL_STEP2 = 2
    HEAL_STEP3 = 3

class Proc:
    def __init__(self, source, target, interval):
        self.state = State.IDLE
        self.source = source
        self.target = target
        self.interval = interval

    def adb_loop(self, func):
        while True:
            yield func()
            time.sleep(self.interval)

    def run(self):
        try:
            if self.source == 'net.raw':
                img_gen = net.read_raw()
            elif self.source == 'net.jpg':
                img_gen = net.read_jpg()
            elif self.source == 'adb.raw':
                img_gen = self.adb_loop(adb.read_raw)
            elif self.source == 'adb.png':
                img_gen = self.adb_loop(adb.read_png)
            else:
                print(f'Unknown source: {self.source}')
                return

            help_time = time.time() * 1000
            chat_time = time.time() * 1000
            for img in img_gen:
                heal_ret = self.do_heal(img)
                help_ret, help_time = self.do_help(img, help_time)
                if (heal_ret + help_ret) < 1:
                    chat_time = self.do_chat(img, chat_time)
        except KeyboardInterrupt:
            pass

    def do_chat(self, img, prev):
        current = time.time() * 1000
        if (current - prev) < 1500:
            return prev

        offset = (-50, 0)
        tpl = template.config[self.target]['chat']['file']
        area = template.config[self.target]['chat']['area']
        pos, con = image.match_tpl(img, tpl, area=area, offset=offset)
        if con > 0.7:
            print(f"😢 In chat {con:.2f} : {pos}")
            adb.click(pos)
            self.state = State.IDLE
            return current
        else:
            return prev

    def do_help(self, img, prev):
        current = time.time() * 1000
        if (current - prev) < 2000:
            return 0, prev

        tpl = template.config[self.target]['help']['file']
        area = template.config[self.target]['help']['area']
        pos, con = image.match_tpl(img, tpl, area=area)
        if con > 0.8:
            print(f"😀 Do help {con:.2f} : {pos}")
            adb.click(pos)
            return 1, current
        else:
            return 0, prev

    def do_heal(self, img):
        match self.state:
            case State.IDLE:
                tpl = template.config[self.target]['heal']['file']
                area = template.config[self.target]['heal']['area']
                offset = (0, 0)
                threshold = 0.7
            case State.HEAL_STEP1:
                tpl = template.config[self.target]['heal_s2']['file']
                area = template.config[self.target]['heal_s2']['area']
                offset = (0, 10)
                threshold = 0.8
            case State.HEAL_STEP2:
                tpl = template.config[self.target]['heal_s3']['file']
                area = template.config[self.target]['heal_s3']['area']
                offset = (0, 0)
                threshold = 0.8
            case _:
                print(f'Unknown state: {self.state}')

        pos, con = image.match_tpl(img, tpl, area=area, offset=offset)
        if con > threshold and self.state == State.IDLE:
            print(f"😀 Do hea1 {con:.2f} : {pos}")
            adb.click(pos)
            self.state = State.HEAL_STEP1
            return 1
        elif con > threshold and self.state == State.HEAL_STEP1:
            print(f"😀 Do hea2 {con:.2f} : {pos}")
            adb.click(pos)
            self.state = State.HEAL_STEP2
            return 1
        elif con > threshold and self.state == State.HEAL_STEP2:
            print(f"😀 Do hea3 {con:.2f} : {pos}")
            adb.click(pos)
            self.state = State.IDLE
            return 1
        else:
            return 0


