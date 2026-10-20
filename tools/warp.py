import glob, json, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_bounds
from rasterio.enums import Resampling as R
from PIL import Image
c = json.load(open('tools/chart.json'))
src_path = sorted(glob.glob('/tmp/wp/**/*.tif', recursive=True), key=lambda p: -__import__('os').path.getsize(p))[0]
print('tif', src_path)
with rasterio.open(src_path) as s:
    print(s.crs, s.width, s.height, s.count, s.dtypes, s.bounds)
    f = max(1, int(s.width / 9000))
    h, w = s.height // f, s.width // f
    tr = s.transform * s.transform.scale(s.width / w, s.height / h)
    bands = s.read(out_shape=(s.count, h, w), resampling=R.nearest)
    if s.count == 1 and s.colorinterp[0].name == 'palette':
        cm = s.colormap(1); lut = np.zeros((256, 3), np.uint8)
        for k, v in cm.items(): lut[k] = v[:3]
        rgb = lut[bands[0]].transpose(2, 0, 1)
    else:
        rgb = bands[:3]
    W, H = c['w'], c['h']
    dt = from_bounds(c['xmin'], c['ymin'], c['xmax'], c['ymax'], W, H)
    out = np.full((3, H, W), 255, np.uint8)
    for i in range(3):
        reproject(rgb[i], out[i], src_transform=tr, src_crs=s.crs, dst_transform=dt, dst_crs=c['proj'], resampling=Resampling.bilinear, src_nodata=None, dst_nodata=255)
img = Image.fromarray(out.transpose(1, 2, 0))
img.save('public/chart.jpg', quality=84, optimize=True)
img.resize((1920, 1080), Image.LANCZOS).save('public/chart-1080.jpg', quality=82, optimize=True)
print('chart written')
