import os


def read_patterns(file):
    if not os.path.isfile(file):
        return []
    with open(file, 'r') as f:
        ls = [l.strip() for l in f.readlines()]
        # filter empty lines
        ls = [l for l in ls if l]
        # filter comments
        ls = [l for l in ls if not l.startswith('#')]
        return ls
