from skimage.filters import difference_of_gaussians, threshold_otsu
from cellSAM import  segment_cellular_image

__all__ = ['simple', 'sam']


def simple(img, sigma1, sigma2):
    img = difference_of_gaussians(img, sigma1, sigma2)
    img = img > threshold_otsu(img)
    return img


def sam(img):
    mask, _, _ = segment_cellular_image(img, normalize=True, device='cuda', fast=True)
    return mask > 0