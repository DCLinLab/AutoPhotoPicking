from img_proc.cell_segment import *
import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
import time
from cellSAM import get_model, segment_cellular_image
from cellSAM.utils import (
    format_image_shape,
    normalize_image,
)
import torch
from rtree import index
from skimage.transform import resize, downscale_local_mean


def sam2(img_in, crystals, scale_factor=4):
    model = get_model(None).eval()
    model.bbox_threshold = 0.4
    img_in = downscale_local_mean(img_in, scale_factor)

    img = format_image_shape(img_in)
    img = normalize_image(img)
    img = img.transpose((2, 0, 1))  # channel first for pytorch.
    img = torch.from_numpy(img).float().unsqueeze(0)

    model, img = model.to('cuda'), img.to('cuda')
    t1 = time.time()
    boxes_per_heatmap = model.generate_bounding_boxes(img, device='cuda')
    t2 = time.time()
    print(f'bbox: {t2-t1}s')
    # filter the boxes
    idx = index.Index()

    scaling = 1024 / max(img.shape)
    boxes1 = []
    for i, coord in enumerate(boxes_per_heatmap[0]):
        x1, y1, x2, y2 = coord.cpu().numpy() // scaling
        idx.insert(i, (x1, y1, x2, y2))
        boxes1.append((x1, y1, x2, y2))
    boxes2 = []
    for y, x in zip(*crystals):
        y /= scale_factor
        x /= scale_factor
        n = list(idx.nearest((x, y, x, y), 1))[0]
        x1, y1, x2, y2 = boxes1[n]
        if y1 <= y <= y2 and x1 <= x <= x2:
            boxes2.append(n)
    if not boxes2:
        return np.zeros(img.shape, dtype=int)
    boxes2 = np.unique(boxes2)
    bbox = [list(boxes1[i]) for i in boxes2]
    mask, _, _ = segment_cellular_image(img_in, device='cuda', normalize=True, bounding_boxes=bbox, fast=True)
    new_shape = (int(mask.shape[0] * scale_factor), int(mask.shape[1] * scale_factor))
    upscaled_mask = resize(mask, new_shape, order=0, preserve_range=True, anti_aliasing=False)
    return upscaled_mask


def img_proc(img):
    # t1 = time.time()
    # model = get_model(None).eval()
    # model.bbox_threshold = 0.4
    #
    # img_ = format_image_shape(img)
    # img_ = normalize_image(img_)
    # img_ = img_.transpose((2, 0, 1))  # channel first for pytorch.
    # img_ = torch.from_numpy(img_).float().unsqueeze(0)
    #
    # model, img_ = model.to('cuda'), img_.to('cuda')
    # boxes_per_heatmap = model.generate_bounding_boxes(img_, device='cuda')
    # t2 = time.time()
    # print(t2 - t1)

    t1 = time.time()
    crystals = detect_crystal(img, 11, 100)
    t2 = time.time()
    print(f'detect: {t2 - t1}s')
    cells = sam2(img, crystals)
    t3 = time.time()
    print(f'segment: {t3 - t2}s')
    img = np.zeros_like(img, dtype=np.uint8)
    for y, x in zip(*crystals):
        i = cells[y, x]
        if i > 0:
            img[cells == i] = i
    return img

if __name__ == '__main__':
    # img1 = imread(r'F:\temp\2024-10-31\new\new_S0000(TR1)_C01(EGFP)_M0001_ORG.jpg')
    img1 = imread(r'F:\temp\2024-11-05\new-02\new_S0000(TR1)_C01(EGFP)_M0003_ORG.jpg')
    # img1 = imread(r'F:\temp\2024-10-27\new-08\new_S0000(TR1)_C01(EGFP)_M0019_ORG.jpg')
    fig, ax = plt.subplots(1, 2, dpi=300)
    ax[0].imshow(img1, cmap='gray')
    ax[0].axis('off')
    ax[1].imshow(img_proc(img1)>0, cmap='gray')
    ax[1].axis('off')
    plt.tight_layout()
    plt.show()

