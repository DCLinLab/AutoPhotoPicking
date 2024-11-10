import time
from segmentation.cell_segment import sam2, detect_crystal
import numpy as np


def get_cells_with_crystal(img, block_size=11, tolerance=100, downscale=2):
    t1 = time.time()
    crystals = detect_crystal(img, block_size, tolerance)
    t2 = time.time()
    print(f'detection time: {t2 - t1:.2f}s')
    cells = sam2(img, crystals, downscale)
    t3 = time.time()
    print(f'segmentation time: {t3 - t2:.2f}s')
    mask = np.zeros_like(img, dtype=bool)
    for y, x in zip(*crystals):
        i = cells[y, x]
        if i > 0:
            mask[cells == i] = True
    return mask