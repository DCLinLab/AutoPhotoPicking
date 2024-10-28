from utils.cell_segment import *
import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread


def img_proc(img):
    cells = sam(img)
    crystals = detect_crystal(img, 11, 100)
    img = np.zeros_like(img, dtype=np.uint8)
    for y, x in zip(*crystals):
        i = cells[y, x]
        if i > 0:
            img[cells == i] = i
    return img

if __name__ == '__main__':
    img1 = imread(r'F:\temp\2024-10-27\new-08\new_S0000(TR1)_C01(EGFP)_M0018_ORG.jpg')
    # img1 = imread(r'F:\temp\2024-10-27\new-08\new_S0000(TR1)_C01(EGFP)_M0019_ORG.jpg')
    fig, ax = plt.subplots(1, 2, dpi=300)
    ax[0].imshow(img1, cmap='gray')
    ax[0].axis('off')
    ax[1].imshow(img_proc(img1), cmap='gray')
    ax[1].axis('off')
    plt.tight_layout()
    plt.show()

