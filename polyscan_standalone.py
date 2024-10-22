import socket
import struct
import numpy as np
import time
import yaml
from skimage.filters import gaussian, threshold_otsu
from skimage.util import img_as_ubyte
from skimage.io import imread
from pathlib import Path
import warnings
from traceback import print_exc


def img_proc(img, sigma):
    img = gaussian(img, sigma)
    t = threshold_otsu(img)
    img = img > t
    return img_as_ubyte(img)


def Convert(img8):
    s = img8.shape
    a = img8.reshape(s[0] * s[1] // 8, 8)
    a2 = np.ones(a.shape)
    for i in range(7):
        a2[:, i] = 1 << (7 - i)
    a = a * a2
    return a.sum(axis=1)


def SoftwareTrigger(s, dev):
    bdev = str.encode(dev)
    blen = len(bdev)
    req = struct.pack('iii' + str(blen) + 's', 12 + blen, 101, blen, bdev)
    s.send(req)
    print("Request 101 sent")


def connect(host, port, port_trigger):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_ip = socket.gethostbyname(host)
    s.connect((remote_ip, port))

    # connect to server
    s_trigger = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_trigger.connect((remote_ip, port_trigger))
    print("Trigger connected to server")
    return s, s_trigger


if __name__ == '__main__':
    # load configuration
    config = 'config/polyscan_standalone.yaml'
    with open(config, 'r') as f:
        config = yaml.safe_load(f)
    scan_interval = config['scan']['interval']
    tdir = Path(config['scan']['dir'])
    sigma = config['img_proc']['sigma']
    key = config['scan']['keyword']
    trigger = config['tcpip']['trigger_name']
    host = config['tcpip']['host']
    port = config['tcpip']['port']
    port_trigger = config['tcpip']['port_trigger']
    # start connection

    # loop
    existing_files = set(str(i) for i in tdir.rglob(f'*{key}*'))
    while True:
        s, s_trigger = connect(host, port, port_trigger)
        try:
            new_files = set(str(i) for i in tdir.rglob(f'*{key}*')) - existing_files
            if len(new_files) > 0:
                existing_files |= new_files
                new_files = [Path(i) for i in new_files]
                if len(new_files) > 1:
                    warnings.warn('More than 1 new image detected, assume the latest one.')
                file = max(new_files, key=lambda p: p.stat().st_mtime)
                print('Detected new image {}'.format(file))
                img = imread(file)
                img = img_proc(img, sigma)
                pat = Convert(img)
                func = np.uint32(2)
                w = np.uint32(img.shape[1])
                h = np.uint32(img.shape[0])
                s.send(func)
                s.send(w)
                s.send(h)
                s.send(pat)
                # software trigger
                SoftwareTrigger(s_trigger, trigger)
            time.sleep(scan_interval)
        except:
            print_exc()
        finally:
            s.close()
    # end connection
    print('over.')
