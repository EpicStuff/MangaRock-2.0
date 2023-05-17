from functools import partial as wrap


def t(a, b):
    print(a, b)


x = wrap(t, 1)

x(3)
