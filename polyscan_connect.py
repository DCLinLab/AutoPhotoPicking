import struct
import socket
import numpy as np


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


class PolyScan:
    def __init__(self, host, port, port_trigger, trigger_name):
        self.remote_ip = socket.gethostbyname(host)
        self.port = port
        self.port_trigger = port_trigger
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_trigger = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.trigger_name = trigger_name

    def connect(self):
        self.s.connect((self.remote_ip, self.port))
        self.s_trigger.connect((self.remote_ip, self.port_trigger))

    def send(self, img):
        img = (img > 0) * np.ones(img.shape)
        pat = Convert(img)
        func = np.uint32(2)
        w = np.uint32(img.shape[1])
        h = np.uint32(img.shape[0])
        self.s.send(func)
        self.s.send(w)
        self.s.send(h)
        self.s.send(pat)
        SoftwareTrigger(self.s_trigger, self.trigger_name)

    def close(self):
        self.s.close()
        self.s_trigger.close()

    def __enter__(self):
        self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()