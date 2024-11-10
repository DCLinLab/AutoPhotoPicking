### -------------------- PreScript ---------------------------------------------- ###


import requests
from time import sleep
import base64
import sys
from skimage.io import imread


sys.path.append('../')

server_url = 'http://127.0.0.1:5000'
detect_track = 2
timeout = 60
exposure_wait = 20

segment_config = {
    'block_size': 11,
    'tolerance': 100,
    'downscale': 2,
    'calibration': (10, 10),
    'save': True,
    'plot': True,
}

polyscan_config = {
    'host': 'localhost',
    'port': 2222,
    'port_trigger': 2228,
    'trigger_name': 'tcp'
}


### -------------------- LoopScript --------------------------------------------- ###


if ZenService.Experiment.CurrentTrackIndex == detect_track:
    ZenService.Actions.PauseExperiment()

    # send image to segment
    fname = ZenService.Experiment.ImageFileName
    img = imread(fname)
    payload = {
        'fname': fname,
        'array': base64.b64encode(img.tobytes()).decode('utf-8'),
        'shape': img.shape,
        'dtype': str(img.dtype),
        'config': segment_config
    }
    response = requests.post(f'{server_url}/segment', json=payload,
                             timeout=timeout)

    if response.status_code == 200:
        response = requests.post(f'{server_url}/trigger', json=polyscan_config)
        sleep(exposure_wait)

    ZenService.Actions.ContinueExperiment()


### -------------------- PostScript --------------------------------------------- ###