from __future__ import print_function

import sys
sys.path.append('../')

from include_lite import *
import simple_district

import pickle, json, fnmatch
from collections import namedtuple

def json_read_obj(f):
    return json.load(f, object_hook = lambda d: namedtuple('X', d.keys())(*d.values()) )

def dump_conf(conf, f):
    json.dump(conf.__dict__, f)

def load_conf(f):
    return json_read_obj(f)

def districts_to_json(dist_arr):
    dd = {}
    dd['code'] = [d.get_code() for d in dist_arr]
    dd['vote'] = [d.get_dem_ratio() for d in dist_arr]

    return dd

def districts_from_json(js):
    assert 'code' in js
    assert 'vote' in js
    assert len(js['code']) == len(js['vote'])

    ret = []
    
    for i in range(len(js['vote'])):
        ret.append(simple_district.SimpleDistrict(js['code'][i], js['vote'][i]))

    return ret

def dump_districts(dist_arr, f):
    json.dump(districts_to_json(dist_arr), f)

def load_districts(f):
    return districts_from_json(json.load(f))

def recursive_files(path):
    for root, directories, filenames in os.walk(path):
        for filename in filenames:
            yield root, filename

def repickle_samples(path):
    for d, f in recursive_files(path):
        
        if fnmatch.fnmatch(f, "z*.pickle"):
            full_in = os.path.join(d, f)
            full_out = os.path.join(d, f.replace('pickle', 'json'))
            
            with open(full_in, 'rb') as fh:
                dist_arr = pickle.load(fh)
                
            with open(full_out, 'w') as fh:
                my_serializer.dump_districts(dist_arr, fh)
                
        if f == 'setup.pickle':
            full_in = os.path.join(d, f)
            full_out = os.path.join(d, f.replace('pickle', 'json'))

            print(full_out)
            
            with open(full_in, 'rb') as fh:
                conf = pickle.load(fh)
                
            with open(full_out, 'w') as fh:
                my_serializer.dump_conf(conf, fh)

if __name__ == '__main__':
    repickle_samples('simulations')
