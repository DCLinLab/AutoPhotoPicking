import configparser
import numpy as np
from skimage.util import img_as_ubyte
import tcpoad
from datetime import date
from pathlib import Path
from czifile import imread
from polyscan_connect import PolyScan
from segmentation import get_cells_with_crystal
import matplotlib.pyplot as plt
from segmentation.checkerboard_pattern import generate_checkerboard_mask
from tifffile import imwrite


def run(cmd, timeout=10):
    ans = []
    for i in cmd.strip().split('\n'):
        ans.append(tcpoad.tcp_eval_expression_and_wait_for_ok(tel, i, timeout)[1])

    return ans


def init():
    cmd = f"""
    exp = Zen.Acquisition.Experiments.GetByName("{config["Experiment"]["name"]}.czexp")
    print(exp.AutoSave.IsActivated)
    """
    if eval(run(cmd)[-1]):
        folder, prefix = eval(run('print(exp.AutoSave.StorageFolder, exp.AutoSave.Name)')[-1])
    else:
        folder, prefix = config['Save']['work_dir'], 'New'
    savedir = Path(folder) / str(date.today())
    i = 1
    while True:
        path = savedir / f'{prefix}-{i:02}'
        if not path.exists():
            break
        i += 1
    path.mkdir(parents=True, exist_ok=True)
    before = config["Save"]["before"]
    after = config["Save"]["after"]
    path1 = path / f'{before}.czi'
    path2 = path / f'{after}.czi'
    cmd = f"""
    {before} = ZenImage()
    {before}.Save(r"{path1}")
    {after} = ZenImage()
    {after}.Save(r"{path2}")
    """
    run(cmd)
    return path


def get_tile_set():
    cmd = f"""
    t = exp.GetTileRegionInfos({config['Experiment']['tile_block']})[{config['Experiment']['tile_array']}]
    print(t.CenterX, t.CenterY, t.Columns, t.Rows, t.Height, t.Width)
    """
    ctx, cty, ncol, nrow, height, width = eval(run(cmd)[-1])
    return float(ctx), float(cty), int(ncol), int(nrow), float(height), float(width)


def scan(x, y, key):
    cmd = f"""
    Zen.Devices.Stage.MoveTo({x}, {y}
    img = Zen.Acquisition.AcquireImage(exp_detect)
    img.Save(r"{temp_path}")
    {key}.AddScene(img, {x}, {y})
    {key}.Save()
    """
    run(cmd)
    return imread(temp_path)[..., 0]


if __name__ == '__main__':
    tel = tcpoad.tcp_open_port()
    config = configparser.ConfigParser()
    config.read('config.conf')
    save_dir = init()
    print(f'Images saved to {save_dir}')
    export_dir = Path(config['Save']['work_dir']) / 'mask'
    temp_path = config['work_dir'] / 'temp.czi'
    ctx, cty, ncol, nrow, height, width = get_tile_set()
    stepx, stepy = width / ncol, height / nrow
    startx, starty = ctx - width / 2, cty - height / 2
    print(f'Tile scanning {nrow}x{ncol} region.\n')

    for i in range(nrow):
        for j in range(ncol):
            currenty = starty + i * stepy
            currentx = startx + j * stepx

            img1 = scan(currentx, currenty, 'before')
            print('Performing segmentation.')
            mask = get_cells_with_crystal(img1[config['Experiment']['detect_channel']],
                                          config['Segmentation']['block_size'],
                                          config['Segmentation']['tolerance'],
                                          config['Segmentation']['downscale'])

            if config.getboolean('Segmentation', 'calibration'):
                a, b = tuple(config['Segmentation']['checkerboard'])
                print(f'Administering checkerboard of {a}x{b}')
                g = generate_checkerboard_mask(mask.shape, a, b)
                mask &= g

            if config.getboolean('Segmentation', 'plot'):
                plt.imshow(mask, cmap='gray')
                plt.axis('off')
                plt.show()

            with PolyScan(**config['PolyScan4']) as p:
                print('Triggering PolyScan.')
                p.send(mask)

            img2 = scan(currentx, currenty, 'after')

            if config.getboolean('Segmentation', 'save'):
                export_dir.mkdir(parents=True, exist_ok=True)
                p = export_dir / f'{i}-{j}.tiff'
                imwrite(p, [img1, img_as_ubyte(mask)[np.newaxis, ...], img2], imagej=True,
                        photometric='minisblack', metadata={'axes': 'CYX'})
                print(f'Exporting mask to {p}')

            print(f'Finished tile ({i}, {j})\n')
