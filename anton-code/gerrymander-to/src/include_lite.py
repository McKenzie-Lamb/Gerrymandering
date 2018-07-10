from __future__ import print_function

import csv
from pprint import pprint
import random

import os
import sys
import json
import copy
import math
import time

def within(val, t, m):
    return abs(val - t) < m


def gaussian_integral(mean, std, a, b):
    def phi(x):
        #'Cumulative distribution function for the standard normal distribution'
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
    a = (a - mean)/std
    b = (b - mean)/std

    return phi(b)-phi(a)

class dummy(object):
    pass

def percent(f):
    return float(round(f*1000))/10
def percent_str(f):
    return str(float(round(f*1000))/10) + '%'

def open_create_file(file_name, suffix):
    if not os.path.exists(os.path.dirname(file_name)):
        os.makedirs(os.path.dirname(file_name))
        
    return open(file_name, 'w')

def path_split(file_name):
    f_dir, f_name = os.path.split(file_name)
    f_base, f_ext = os.path.splitext(f_name)

    return f_dir, f_base, f_ext

def path_join(f_dir, f_base, f_ext):
    return os.path.join(f_dir, f_base + f_ext)
    
def folder_prep(out_name):
    if not os.path.exists(os.path.dirname(out_name)):
        os.makedirs(os.path.dirname(out_name))

def nCr(n,r):
    if r == -1:
        return 0
    f = math.factorial
    return f(n) / f(r) / f(n-r)


def time_fn(fn, *args):
    start = time.time()
    ret = fn(*args)
    end = time.time()
    print(fn.__name__, "time:", round(end - start, 2), "sec")
    return ret, end - start

class UpdateTime:
    def __init__(self, interval):
        self.interval = interval
        self.time = time.time()

    def is_update_time(self):
        now = time.time()
        if now - self.time > self.interval:
            self.time = now
            return True
        else:
            return False
    


def almost_equal(a, b):
    return abs(a - b) <= .00001

def avg(arr):
    return sum(arr)/len(arr)

class jsonobj:
    def __init__(self, dct):
        for k in dct:
            setattr(self, k, dct[k])
    
    @staticmethod
    def load(f):
        return json.load(f, object_hook=lambda d: jsonobj(d))
    
    @staticmethod
    def dump(obj, f, indent=None):
        json.dump(obj, f, default = lambda o: o.__dict__, indent=indent, sort_keys=True)

    @staticmethod
    def dumps(obj, indent=None):
        return json.dumps(obj, default = lambda o: o.__dict__, indent=indent, sort_keys=True)

