#!/usr/bin/env bash
# Render build step: fetch FAA U.S. VFR Wall Planning Chart GeoTIFF (public domain) and warp it to the display projection.
# Never fails the build; the page falls back to a plain state-line map if the chart is missing.
set -u; cd "$(dirname "$0")/.."
[ -s public/chart.jpg ] && { echo "chart already present"; exit 0; }
U=$(curl -s -m 20 "https://external-api.faa.gov/apra/vfr/wallplanning/chart?edition=current&format=tiff&geoname=US" -H "Accept: application/json" | python3 -c "import sys,json;print(json.load(sys.stdin)['edition'][0]['product']['url'])" 2>/dev/null)
[ -n "$U" ] || U="https://web.archive.org/web/20260329031553id_/https://aeronav.faa.gov/visual/03-19-2026/Planning/US_WallPlan.zip"
echo "chart source: $U"
mkdir -p /tmp/wp && curl -sSL --retry 4 -m 600 -o /tmp/wp/wp.zip "$U" && (cd /tmp/wp && python3 -m zipfile -e wp.zip . ) && ls -la /tmp/wp || { echo "chart download failed"; exit 0; }
python3 -m pip install -q --user rasterio numpy pillow 2>&1 | tail -2 || { echo "pip failed"; exit 0; }
python3 tools/warp.py || echo "warp failed"
exit 0
