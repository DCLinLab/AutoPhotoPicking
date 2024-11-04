from cellSAM import segment_cellular_image, get_model
from skimage.filters import difference_of_gaussians, threshold_otsu, threshold_local
from skimage.util import img_as_ubyte
from scipy.ndimage import generate_binary_structure
from findmaxima2d import find_maxima, find_local_maxima
from .gwdt import gwdt
from rtree import index
from skimage.transform import resize, downscale_local_mean
import numpy as np

from cellSAM.utils import (
    format_image_shape,
    normalize_image,
)

import torch


__all__ = ['simple', 'sam', 'detect_crystal']


def simple(img, sigma1, sigma2):
    img = difference_of_gaussians(img, sigma1, sigma2)
    img = img > threshold_otsu(img)
    return img


def detect_crystal(img, block_size=11, tolerance=10):
    fg = (img - threshold_local(img, block_size)).clip(0)
    fg = img_as_ubyte(fg / fg.max())
    structure = generate_binary_structure(img.ndim, 10)
    dt = gwdt(fg, structure)
    y, x, _ = find_maxima(dt, find_local_maxima(dt), tolerance)
    return y, x


def sam(img):
    mask, _, _ = segment_cellular_image(img, fast=True, device='cuda', normalize=True)
    return mask


def sam2(img_in, crystals, scale_factor=4):
    model = get_model(None).eval()
    model.bbox_threshold = 0.4
    img_in = downscale_local_mean(img_in, scale_factor)

    img = format_image_shape(img_in)
    img = normalize_image(img)
    img = img.transpose((2, 0, 1))  # channel first for pytorch.
    img = torch.from_numpy(img).float().unsqueeze(0)

    model, img = model.to('cuda'), img.to('cuda')
    boxes_per_heatmap = model.generate_bounding_boxes(img, device='cuda')
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
