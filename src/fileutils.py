#!/usr/bin/env python

import os

def get_real_fname():
    absfname = os.path.abspath(__file__)
    if os.path.islink(absfname):
        absfname = os.path.realpath(absfname)
    return  absfname

def get_base_parent_path():
    fname = get_real_fname()
    fpath = os.path.dirname(fname)
    return os.path.split(fpath)[0]

def test():
    rpath, rfname = os.path.split(get_real_fname())
    print "Real name = {}\nReal base = {}".format(rfname, rpath)

if __name__ == "__main__":
    test()

