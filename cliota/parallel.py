import multiprocessing


def fun(f, q_in, q_out):
    while True:
        i, x = q_in.get()
        if i is None:
            break
        q_out.put((i, f(*x) if type(x) is tuple else f(x)))


def parmap(f, X, nprocs=multiprocessing.cpu_count()):
    q_in = multiprocessing.Queue(1)
    q_out = multiprocessing.Queue()

    proc = [multiprocessing.Process(target=fun, args=(f, q_in, q_out))
            for _ in range(nprocs)]
    for p in proc:
        p.start()

    sent = [q_in.put((i, x)) for i, x in enumerate(X)]
    [q_in.put((None, None)) for _ in range(nprocs)]
    res = [q_out.get() for _ in range(len(sent))]

    [p.join() for p in proc]

    return [x for i, x in sorted(res)]


def funcparallel(funcs, X):
    def fun_once(f, i, x, q_out):
        q_out.put((i, f(x)))

    q_out = multiprocessing.Queue()

    proc = [multiprocessing.Process(target=fun_once, args=(funcs[i], i, X[i], q_out))
            for i in range(len(funcs))]
    for p in proc:
        p.start()

    res = [q_out.get() for _ in range(len(funcs))]

    [p.join() for p in proc]

    return [x for i, x in sorted(res, key=lambda x: x[0])]
