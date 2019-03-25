import os
import ee
import json
from glob import glob
from kml2geojson import convert

def fix_geojson(geojson):
    # These points have three coordinates (lng, lat, alt),
    # EE wants only the first two
    for feat in geojson['features']:
        if feat['geometry']['type'] == 'Point':
            feat['geometry']['coordinates'] = feat['geometry']['coordinates'][:2]
    return geojson

ee.Initialize()
feats = {}
out_path = '/tmp'
for kml_path in glob('DRC_Cobalt_KMLs/*.kml'):
    convert(kml_path, out_path)
    fname = os.path.basename(kml_path)
    fname = fname.replace(' ', '_')
    key = fname.split('.')[0]
    gj_path = os.path.join(out_path, fname.replace('.kml', '.geojson'))
    geojson = json.load(open(gj_path))
    geojson = fix_geojson(geojson)
    feats[key] = ee.FeatureCollection(geojson['features'])