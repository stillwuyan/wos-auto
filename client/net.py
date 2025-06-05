import urllib.request
import struct
import image

# adb forward tcp:8080 tcp:8080
url = "http://127.0.0.1:8080"

def read_jpg():
    stream = urllib.request.urlopen(url)
    bytes_data = bytes()
    while True:
        bytes_data += stream.read(1024)
        a = bytes_data.find(b'\xff\xd8')
        b = bytes_data.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg_frame = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            yield image.parse_img(jpg_frame)
    stream.close()

def read_raw():
    stream = urllib.request.urlopen(url)
    data = bytes()
    while True:
        data = stream.read(1024)
        if len(data) < 1024:
            print('invalid data', data)
            break

        pos = data.find(b'Content-Length:')
        pos = data.find(b'\r\n', pos+1)
        if pos == -1:
            print('invalid header')
            break

        offset = 16
        header = data[pos+2:pos+2+offset]
        width, height, padding, size = struct.unpack('!iiii', header)

        if (width > 2000):
            print('invalid width', data)
            break

        payload = data[pos+2+offset:]
        payload += stream.read(size - len(payload))
        #print(width, height, padding, size, len(payload))
        yield image.parse_raw(payload, 'RGBA_8888', width, height, padding)
    stream.close()
