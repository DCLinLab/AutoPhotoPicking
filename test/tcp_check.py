import tcpoad


if __name__ == '__main__':
    t = tcpoad.tcp_open_port()
    print(t)
    ok = tcpoad.tcp_eval_expression_and_wait_for_ok(t, """print('123')""", 1)
    print(ok)