# Build a deep-zoom tile pyramid of the CURRENT FAA VFR Sectional rasters (public domain, aeronav.faa.gov),
# mosaicked into the app's Lambert Conformal Conic display frame so METAR dots (projected in the browser) line up.
# Usage: python3 tools/build_tiles.py <dir-with-SEC.tif> <edition MM-DD-YYYY> [maxlevel]
import glob, json, os, sys, math, numpy as np, rasterio
from concurrent.futures import ProcessPoolExecutor
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from rasterio.warp import transform as wtr
from PIL import Image
SRC, ED = sys.argv[1], sys.argv[2]; MAXL = int(sys.argv[3]) if len(sys.argv) > 3 else 4
ROOT = os.path.join(os.path.dirname(__file__), '..', 'public'); OUT = os.path.join(ROOT, 'tiles')
FR = dict(lat1=45, lat2=33, lat0=38, lon0=-100, xmin=-2131062.18, xmax=2610537.27, ymin=-1310255.88, ymax=1356893.81)
CRS = f"+proj=lcc +lat_1={FR['lat1']} +lat_2={FR['lat2']} +lat_0={FR['lat0']} +lon_0={FR['lon0']} +datum=WGS84 +units=m +no_defs"
T = 512; W0 = 3840  # level 0 is 3840 px wide (4K full view); each level doubles
CLIPS = json.load(open(os.path.join(os.path.dirname(__file__), 'sectional_clips.json')))
def lvl_size(l): w = W0 * 2**l; return w, round(w * (FR['ymax']-FR['ymin']) / (FR['xmax']-FR['xmin']))
charts = []
for f in sorted(glob.glob(os.path.join(SRC, '*SEC.tif'))):
    n = os.path.basename(f)[:-8].replace(' ', '_')
    poly = CLIPS.get(n)
    if not poly: print('no clip for', n); continue
    dens = []  # densify edges so parallels curve correctly in the LCC frame
    for (a, b), (c, d) in zip(poly, poly[1:] + poly[:1]):
        for k in range(20): dens.append((a + (c-a)*k/20, b + (d-b)*k/20))
    xs, ys = wtr('EPSG:4326', CRS, [p[0] for p in dens], [p[1] for p in dens])
    charts.append((f, list(zip(xs, ys)), (min(xs), min(ys), max(xs), max(ys))))
def tile(args):
    tx, ty = args; l = MAXL; w, h = lvl_size(l); mpp = (FR['xmax']-FR['xmin'])/w
    x0 = FR['xmin'] + tx*T*mpp; y1 = FR['ymax'] - ty*T*mpp; x1, y0 = x0 + T*mpp, y1 - T*mpp
    tr = from_bounds(x0, y0, x1, y1, T, T); rgb = None
    for f, poly, (bx0, by0, bx1, by1) in charts:
        if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1: continue
        m = rasterize([({'type': 'Polygon', 'coordinates': [poly]}, 1)], out_shape=(T, T), transform=tr).astype(bool)
        if not m.any(): continue
        with rasterio.open(f) as s, WarpedVRT(s, crs=CRS, transform=tr, width=T, height=T, resampling=Resampling.nearest if s.count == 1 else Resampling.bilinear) as v:
            a = v.read()
            if s.count == 1:
                cm = s.colormap(1); lut = np.zeros((256, 3), np.uint8)
                for k, c in cm.items(): lut[k] = c[:3]
                px = lut[a[0]]
            else: px = a[:3].transpose(1, 2, 0)
        if rgb is None: rgb = np.full((T, T, 3), (233, 224, 198), np.uint8)
        rgb[m] = px[m]
    if rgb is None: return None
    d = os.path.join(OUT, str(l), str(ty)); os.makedirs(d, exist_ok=True)
    Image.fromarray(rgb).save(os.path.join(d, f'{tx}.webp'), quality=55, method=4); return (tx, ty)
def down(l, tx, ty):  # build level l tile from 4 children of level l+1
    im = Image.new('RGB', (2*T, 2*T), (233, 224, 198)); any_ = False
    for dy in (0, 1):
        for dx in (0, 1):
            p = os.path.join(OUT, str(l+1), str(2*ty+dy), f'{2*tx+dx}.webp')
            if os.path.exists(p): im.paste(Image.open(p).convert('RGB'), (dx*T, dy*T)); any_ = True
    if not any_: return
    d = os.path.join(OUT, str(l), str(ty)); os.makedirs(d, exist_ok=True)
    im.resize((T, T), Image.LANCZOS).save(os.path.join(d, f'{tx}.webp'), quality=65, method=4)
def downargs(a): down(*a)
if __name__ == '__main__':
    import shutil; shutil.rmtree(OUT, ignore_errors=True)
    w, h = lvl_size(MAXL); jobs = [(x, y) for y in range(math.ceil(h/T)) for x in range(math.ceil(w/T))]
    if os.environ.get('ONLY'): jobs = [tuple(map(int, os.environ['ONLY'].split(',')))]
    with ProcessPoolExecutor(int(os.environ.get('JOBS', 8))) as ex:
        done = sum(1 for r in ex.map(tile, jobs, chunksize=4) if r)
    print('max level tiles', done)
    for l in range(MAXL-1, -1, -1):
        w, h = lvl_size(l)
        with ProcessPoolExecutor(8) as ex: list(ex.map(downargs, [(l, x, y) for y in range(math.ceil(h/T)) for x in range(math.ceil(w/T))]))
    # flattened full-view images for instant first paint
    w, h = lvl_size(0); im = Image.new('RGB', (w, h), (233, 224, 198))
    for y in range(math.ceil(h/T)):
        for x in range(math.ceil(w/T)):
            p = os.path.join(OUT, '0', str(y), f'{x}.webp')
            if os.path.exists(p): im.paste(Image.open(p).convert('RGB'), (x*T, y*T))
    im.save(os.path.join(ROOT, 'chart.jpg'), quality=85); im.resize((1920, 1080), Image.LANCZOS).save(os.path.join(ROOT, 'chart-1080.jpg'), quality=85)
    cfg = dict(FR, w=W0, h=lvl_size(0)[1], tile=T, maxLevel=MAXL, tileExt='webp',
               source='FAA VFR Sectional Aeronautical Charts (GeoTIFF), aeronav.faa.gov', edition=ED,
               sourceUrl=f'https://aeronav.faa.gov/visual/{ED}/sectional-files/', nativeMetersPerPixel=42.33,
               maxMetersPerPixel=round((FR['xmax']-FR['xmin'])/lvl_size(MAXL)[0], 1))
    json.dump(cfg, open(os.path.join(ROOT, 'chart.json'), 'w'), indent=1); print(cfg)
