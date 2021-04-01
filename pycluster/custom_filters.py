import os
import random


__all__ = [
    'setup_filters',
    'filter_filesize',
    'filter_randomint',
    'filter_randomfloat',
    'filter_readtxt'
]


def setup_filters(env):
    env.filters['splitext'] = os.path.splitext
    env.filters['filesize'] = filter_filesize
    env.filters['randomint'] = filter_randomint
    env.filters['randomfloat'] = filter_randomfloat
    env.filters['readtxt'] = filter_readtxt
    return env


def filter_filesize(fname):
    return os.path.getsize(fname)


def _helper_random(x, seed, generator, datatype):
    if seed is not None:
        random.seed(seed)
    if isinstance(x, list):
        return generator(datatype(x[0]), datatype(x[1]))
    else:
        return generator(0, datatype(x))


def filter_randomint(x, seed=None):
    return _helper_random(x, seed, random.randint, int)


def filter_randomfloat(x, seed=None):
    return _helper_random(x, seed, random.uniform, float)


def filter_readtxt(arg):
    if type(arg) is not list:
        arg = [arg]
    with open(arg[0], 'r') as fp:
        lines = fp.readlines()
        if len(arg) == 2:
            return lines[arg[1]-1]
        else:
            return ' '.join(lines)

