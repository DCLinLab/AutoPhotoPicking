import numpy as np
import matplotlib.pyplot as plt


def generate_checkerboard_mask(size, nrow, ncol):
    """
    Generate a checkerboard mask.

    Parameters:
    - size: Tuple (height, width) of the mask.
    - nrow: Number of rows in the checkerboard.
    - ncol: Number of columns in the checkerboard.

    Returns:
    - A checkerboard mask as a 2D numpy array.
    """
    # Calculate the height and width of each square in the checkerboard
    square_height = size[0] // nrow
    square_width = size[1] // ncol

    # Create an empty mask
    mask = np.zeros(size, dtype=np.uint8)

    # Fill the mask with the checkerboard pattern
    for i in range(nrow):
        for j in range(ncol):
            if (i + j) % 2 == 0:
                mask[i * square_height:(i + 1) * square_height,
                j * square_width:(j + 1) * square_width] = 1

    return mask

if __name__ == '__main__':
    # Example usage
    mask_size = (400, 400)
    nrows = 8
    ncols = 8
    checkerboard_mask = generate_checkerboard_mask(mask_size, nrows, ncols)

    # Display the mask
    plt.imshow(checkerboard_mask, cmap='gray')
    plt.title('Checkerboard Mask')
    plt.axis('off')
    plt.show()
