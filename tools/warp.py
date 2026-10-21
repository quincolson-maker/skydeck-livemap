# Crop the FAA chart in its NATIVE Lambert projection (no resampling rotation) to a 16:9 CONUS frame,
# and write public/chart.json with the projection parameters so the browser can place stations exactly.
import glob, json, os, numpy as np, rasterio
from rasterio.windows import from_bounds as win_from_bounds
from rasterio.enums import Resampling as R
from rasterio.warp import transform as wtransform
from PIL import Image
src = sorted(glob.glob('/tmp/wp/**/*.tif', recursive=True), key=lambda p: -os.path.getsize(p))[0]
W, H = 3840, 2160
with rasterio.open(src) as s:
    d = s.crs.to_dict(); print(d, s.width, s.height, s.bounds)
    pts = [(48.4,-124.7),(32.5,-117.1),(25.9,-97.4),(24.5,-81.8),(47.4,-67.0),(49.4,-95.1),(40.4,-124.4),(44.8,-66.9),(25.1,-80.4)]
    xs, ys = wtransform('EPSG:4326', s.crs, [p[1] for p in pts], [p[0] for p in pts])
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    padx, pady = (x1-x0)*0.03, (y1-y0)*0.06
    x0 -= padx; x1 += padx; y0 -= pady*1.6; y1 += pady   # extra room at the bottom for the legend/plan cards
    cx, cy, w, h = (x0+x1)/2, (y0+y1)/2, x1-x0, y1-y0
    b = s.bounds; m = (b.right-b.left)*0.012   # fill the TV edge-to-edge with the chart sheet (trim the collar)
    sx0, sx1 = max(b.left+m, cx-h*16/9/2), min(b.right-m, cx+h*16/9/2)
    cx, w = (sx0+sx1)/2, sx1-sx0; h = w*9/16
    cy = max(min(cy, b.top-m-h/2), b.bottom+m+h/2)
    x0, x1, y0, y1 = cx-w/2, cx+w/2, cy-h/2, cy+h/2
    win = win_from_bounds(x0, y0, x1, y1, s.transform)
    bands = s.read(window=win, out_shape=(s.count, H, W), resampling=R.bilinear if s.count >= 3 else R.nearest, boundless=True, fill_value=0)
    if s.count == 1 and s.colorinterp[0].name == 'palette':
        cm = s.colormap(1); lut = np.full((256, 3), 255, np.uint8)
        for k, v in cm.items(): lut[k] = v[:3]
        rgb = lut[bands[0]]
    else:
        rgb = bands[:3].transpose(1, 2, 0)
fe, fn = d.get('x_0', 0), d.get('y_0', 0)
cfg = {"lat1": d.get('lat_1'), "lat2": d.get('lat_2', d.get('lat_1')), "lat0": d.get('lat_0'), "lon0": d.get('lon_0'),
       "xmin": x0-fe, "xmax": x1-fe, "ymin": y0-fn, "ymax": y1-fn, "w": W, "h": H, "crs": s.crs.to_wkt()[:400]}
json.dump(cfg, open('public/chart.json', 'w'), indent=1); print(cfg)
img = Image.fromarray(rgb)
img.save('public/chart.jpg', quality=84, optimize=True)
img.resize((1920, 1080), Image.LANCZOS).save('public/chart-1080.jpg', quality=84, optimize=True)
print('chart written')
