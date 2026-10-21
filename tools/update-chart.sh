#!/usr/bin/env bash
# Update the map to the CURRENT FAA VFR Sectional edition (56-day cycle). Run on any Linux box with python3 + rasterio, pillow, numpy and gh (logged in).
#   bash tools/update-chart.sh            # current edition from the FAA API
#   bash tools/update-chart.sh 10-29-2026 # or a specific edition (MM-DD-YYYY)
# Steps: download 37 CONUS sectional GeoTIFFs from aeronav.faa.gov -> build tile pyramid -> upload as GitHub Release asset
# -> point tools/chart-release.txt at it -> commit. Then push and redeploy on Render.
set -euo pipefail; cd "$(dirname "$0")/.."
ED=${1:-}
if [ -z "$ED" ]; then
  ED=$(curl -s "https://external-api.faa.gov/apra/vfr/sectional/info?edition=current&geoname=Chicago" -H "Accept: application/json" | grep -o '"editionDate":"[^"]*"' | head -1 | cut -d\" -f4 | tr / -)
fi
echo "FAA sectional edition: $ED"
W=/tmp/faa-sec-$ED; mkdir -p $W/x
NAMES="Albuquerque Atlanta Billings Brownsville Charlotte Cheyenne Chicago Cincinnati Dallas-Ft_Worth Denver Detroit El_Paso Great_Falls Green_Bay Halifax Houston Jacksonville Kansas_City Klamath_Falls Lake_Huron Las_Vegas Los_Angeles Memphis Miami Montreal New_Orleans New_York Omaha Phoenix Salt_Lake_City San_Antonio San_Francisco Seattle St_Louis Twin_Cities Washington Wichita"
for n in $NAMES; do echo $n; done | xargs -P 6 -I{} sh -c "[ -s $W/{}.zip ] || curl -fsS -A Mozilla/5.0 --retry 3 -o $W/{}.zip https://aeronav.faa.gov/visual/$ED/sectional-files/{}.zip"
for z in $W/*.zip; do unzip -oq "$z" -d $W/x; done
python3 tools/build_tiles.py $W/x $ED 4
TAR=/tmp/chart-tiles-$ED.tar; tar -C public -cf $TAR tiles
gh release create chart-$ED $TAR -R quincolson-maker/skydeck-livemap -t "FAA VFR Sectional tiles $ED" -n "Tile pyramid built from FAA VFR Sectional GeoTIFFs, edition $ED (aeronav.faa.gov, public domain)." || gh release upload chart-$ED $TAR -R quincolson-maker/skydeck-livemap --clobber
echo "https://github.com/quincolson-maker/skydeck-livemap/releases/download/chart-$ED/chart-tiles-$ED.tar" > tools/chart-release.txt
git add tools/chart-release.txt public/chart.json public/chart.jpg public/chart-1080.jpg && git commit -m "Chart: FAA VFR Sectional edition $ED"
echo "Done. git push, then trigger a Render deploy."
