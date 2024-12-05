from tcpoad import tcp_open_port, tcp_eval_expression_and_wait_for_ok
from pathlib import Path


if __name__ == '__main__':
    tel = tcp_open_port()
    temp_dir = Path('F:/temp')

    commandlist = ['exp = Zen.Acquisition.Experiments.GetByName("AutoPhotoPicking_DETECT.czexp")',
                   'img = Zen.Acquisition.AcquireImage(exp)',
                   f'img.Save(r"{temp_dir / "test.png"}")']

    for i in commandlist:
        print(i)
        ok = tcp_eval_expression_and_wait_for_ok(tel, i, 200)
        print(ok)