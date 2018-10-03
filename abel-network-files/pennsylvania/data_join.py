import fiona
import pprint
import pandas as pd

shapefile = ('data/VTDS.shp')

def join_data(data):
    with fiona.open(shapefile) as shapes:
        for feat in shapes[:1]:
            properties = eval(str(feat['properties'])[7:].lower())
            print(properties)
            data[int(properties['geoid10'])]['pop'] = int(properties['tapersons'])
            data[int(properties['geoid10'])]['geo'] = feat['geometry']

data = dict()
join_data(data)