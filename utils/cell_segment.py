from cellSAM import segment_cellular_image
from skimage.filters import difference_of_gaussians, threshold_otsu, threshold_local
from skimage.util import img_as_ubyte
from scipy.ndimage import generate_binary_structure
from findmaxima2d import find_maxima, find_local_maxima
from .gwdt import gwdt


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
