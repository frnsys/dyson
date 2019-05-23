import re
import os
import zipfile
import requests
from PIL import Image
from tqdm import tqdm
from functools import partial

DOCID_RE = re.compile('docid=([a-z0-9]+)')


def download(url, outfile):
    """download a file"""
    fname = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(outfile, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    # f.flush()
    return outfile


def download_ee_image_zip(url, dir='img'):
    if not os.path.exists(dir):
        os.makedirs(dir)
    id = DOCID_RE.search(url).group(1)
    outdir = os.path.join(dir, id)
    outfile = os.path.join(dir, '{}.zip'.format(id))
    download(url, outfile)
    zfile = zipfile.ZipFile(outfile)
    zfile.extractall(outdir)
    R = Image.open(os.path.join(outdir, '{}.vis-red.tif'.format(id)))
    G = Image.open(os.path.join(outdir, '{}.vis-green.tif'.format(id)))
    B = Image.open(os.path.join(outdir, '{}.vis-blue.tif'.format(id)))
    im = Image.merge('RGB', (R,G,B))
    imname = '{}.png'.format(id)
    impath = os.path.join(dir, imname)
    im.save(impath, optimize=False, compress_level=0)
    os.remove(outfile)
    return id, imname


def get_image_region(ic, feat):
    """Get RGB bands for image region intersecting
    w/ this feature's geometry"""
    return ic.filter(ee.Filter.geometry(ee.Feature(feat).geometry())).median()\
        .visualize(min=0, max=3000, bands=['red', 'green', 'blue'])


def get_images(ic, feats, radius=0.02, scale=30, chunk_size=10):
    images = []
    n_feats = feats.size().getInfo()
    moves = [(radius, radius), (radius, -radius), (-radius, -radius), (-radius, radius)]

    # Process in chunks to avoid
    # exhausing EE memory
    for i in range(n_feats//chunk_size + 1):
        fs = feats.toList(chunk_size, i*chunk_size)
        regions = fs.map(partial(get_image_region, ic))

        # Need to do this to iterate over them
        n_fs = fs.size().getInfo()

        for i in range(n_fs):
            feat = ee.Feature(fs.get(i))
            data = feat.getInfo()
            point = data['geometry']['coordinates']
            bounds = [[point[0]+r0, point[1]+r1] for r0, r1 in moves]
            url = ee.Image(regions.get(i)).getDownloadURL(params={'region': bounds, 'scale': scale})
            images.append((url, data))
    return images



if __name__ == '__main__':
    import json
    from glob import glob
    from main import ee, feats, l8sr
    print(feats.keys())

    # Download image regions for each feature
    for name, features in tqdm(feats.items()):
        for url, data in tqdm(get_images(l8sr, features), desc=name):
            imgid = DOCID_RE.search(url).group(1)
            if os.path.exists(os.path.join('data', imgid)):
                continue
            imgid, imgname = download_ee_image_zip(url, 'data')
            data['id'] = imgid
            data['type'] = name
            data['img'] = imgname
            json.dump(data, open('data/{}/meta.json'.format(imgid), 'w'))

    # Aggregate data
    dataset = {}
    for f in glob('data/**/meta.json'):
        d = json.load(open(f))
        dataset[d['id']] = d
    with open('data/dataset.json', 'w') as f:
        json.dump(dataset, f)
