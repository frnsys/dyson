import os
import re
import ee
import json
import lxml.html
from glob import glob
from kml2geojson import convert

def fix_geojson(geojson):
    # These points have three coordinates (lng, lat, alt),
    # EE wants only the first two
    for feat in geojson['features']:
        if feat['geometry']['type'] == 'Point':
            feat['geometry']['coordinates'] = feat['geometry']['coordinates'][:2]

        # Clean up description to just have the site name
        desc = feat['properties']['description']
        desc = desc.replace('*{font-family:Verdana,Arial,Helvetica,Sans-Serif;}', '')
        html = lxml.html.fromstring(desc)
        text = ''.join(html.itertext())
        text = re.findall('(.+)latitude', text)[0].strip()
        texts = text.split('\xa0')
        feat['properties']['description'] = texts
    return geojson


def maskClouds(image):
    # Bits 3 and 5 are cloud shadow and cloud, respectively.
    cloudShadowBitMask = (1 << 3)
    cloudsBitMask = (1 << 5)

    # Get the pixel QA band.
    qa = image.select('pixel_qa')

    # Both flags should be set to zero, indicating clear conditions.
    mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(qa.bitwiseAnd(cloudsBitMask).eq(0))
    return image.updateMask(mask)


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


# Using Landsat 8 Surface Reflectance Tier 1
# Resolution of 30m^2
# <https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C01_T1_SR>
l8sr = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')

# Rename band names
# (see prev link for reference)
band_names = {
    'B1': 'ultra_blue',
    'B2': 'blue',
    'B3': 'green',
    'B4': 'red',
    'B5': 'nir',
    'B6': 'swir_1',
    'B7': 'swir_2',

    # Not in this dataset
    #'B8': 'pan',
    #'B9': 'cirrus',

    'B10': 'tirs_1',
    'B11': 'tirs_2',
    'sr_aerosol': 'sr_aerosol',
    'pixel_qa': 'pixel_qa',
    'radsat_qa': 'radsat_qa'
}
old_names = ee.List(list(band_names.keys()))
new_names = ee.List(list(band_names.values()))
l8sr = l8sr.select(old_names, new_names).map(maskClouds)