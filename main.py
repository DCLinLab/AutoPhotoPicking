import numpy as np
import base64
from flask import Flask, request, session
from polyscan_connect import PolyScan
from segmentation import get_cells_with_crystal
import matplotlib.pyplot as plt
from skimage.util import img_as_ubyte
from skimage.io import imsave
from segmentation.checkerboard_pattern import generate_checkerboard_mask

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False


@app.post('/segment')
def segment():
    try:
        data = request.get_json()
        shape = tuple(data.get("shape"))
        dtype = data.get("dtype")
        config = data.get("config")
        fname = data.get("fname")
        img = np.frombuffer(base64.b64decode(data.get("array")),
                            dtype=dtype).reshape(shape)

        block_size = config.get("block_size")
        tolerance = config.get("tolerance")
        downscale = config.get("downscale")
        mask = session['img'] = get_cells_with_crystal(img, block_size, tolerance, downscale)

        if 'calibration' in config:
            nrow, ncol = tuple(config['calibration'])
            g = generate_checkerboard_mask(shape, nrow, ncol)
            mask &= g

        if 'plot' in config and config['plot']:
            plt.imshow(mask, cmap='gray')
            plt.axis('off')
            plt.show()

        if 'save' in config and config['save']:
            imsave(f'{fname}_seg.png', img_as_ubyte(mask))
    except:
        return {'status': 'failed'}, 400
    return {'status': 'ok'}, 200


@app.post('/trigger')
def trigger():
    config = request.get_json()
    with PolyScan(**config) as p:
        p.send(session['img'])
    return {'status': 'ok'}, 200

