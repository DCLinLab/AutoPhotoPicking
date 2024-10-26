

def simple(img):
    img = difference_of_gaussians(img, sigma1, sigma2)
    img = img > threshold_otsu(img)
    return img