import socket
import struct

import numpy as np
import time
import yaml
from skimage.data import checkerboard
from img_proc.cell_segment import sam2, detect_crystal
from skimage.io import imread, imsave
from pathlib import Path
import warnings
from traceback import print_exc
from datetime import datetime
from skimage.util import img_as_ubyte
from img_proc.checkerboard_pattern import generate_checkerboard_mask
import matplotlib.pyplot as plt
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError


def with_timeout(func, args=(), kwargs=None, timeout=5):
    if kwargs is None:
        kwargs = {}

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            result = future.result(timeout=timeout)
        except TimeoutError:
            result = None

    return result


def img_proc(img):
    # cells = simple(img, sigma1, sigma2)
    t1 = time.time()
    crystals = detect_crystal(img, block_size, tolerance)
    t2 = time.time()
    print(f'detection time: {t2 - t1}s')
    cells = sam2(img, crystals, downscale)
    t3 = time.time()
    print(f'segmentation time: {t3 - t2}s')
    img = np.zeros_like(img, dtype=bool)
    for y, x in zip(*crystals):
        i = cells[y, x]
        if i > 0:
            img[cells == i] = True
    if checkerboard:
        g = generate_checkerboard_mask(img.shape, nrow, ncol)
        img &= g
    if debug:
        plt.imshow(img, cmap='gray')
        plt.axis('off')
        plt.show()
    imsave(save_dir / (datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.png'), img_as_ubyte(img))
    return img * np.ones(img.shape)


def Convert(img):
    width = img.shape[1]
    n = width % 8
    if n != 0:
        pad = np.zeros((img.shape[0], 8 - n), dtype=np.uint8)
        img = np.hstack((img, pad))
    a = img.reshape(img.size // 8, 8)
    a2 = np.ones_like(a)
    for i in range(7):
        a2[:, i] = 1 << (7 - i)
    a = a * a2
    return a.sum(axis=1).astype('uint8')


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
    # print("Trigger connected to server")
    return s, s_trigger


if __name__ == '__main__':
    # load configuration
    config = 'config/polyscan_standalone.yaml'
    with open(config, 'r') as f:
        config = yaml.safe_load(f)
    scan_interval = config['scan']['interval']
    tdir = Path(config['scan']['dir'])
    timeout = config['scan']['timeout']
    # sigma1 = config['img_proc']['sigma1']
    # sigma2 = config['img_proc']['sigma2']
    block_size = config['img_proc']['block_size']
    tolerance = config['img_proc']['tolerance']
    wrad = config['img_proc']['wrad']
    downscale = config['img_proc']['downscale']
    key = config['scan']['keyword']
    trigger = config['tcpip']['trigger_name']
    host = config['tcpip']['host']
    port = config['tcpip']['port']
    port_trigger = config['tcpip']['port_trigger']
    debug = config['img_proc']['debug']
    checkerboard = config['img_proc']['checkerboard']
    nrow = config['img_proc']['checkerboard_row']
    ncol = config['img_proc']['checkerboard_col']
    save_dir = Path(config['img_proc']['save_dir'])
    save_dir.mkdir(exist_ok=True, parents=True)

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
                img = with_timeout(img_proc, args=(img,), timeout=timeout)
                if img is None:
                    print('timeout, skipping..')
                    continue
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
        except:
            print_exc()
        finally:
            s.close()
            s_trigger.close()
        time.sleep(scan_interval)
