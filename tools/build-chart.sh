#!/usr/bin/env bash
# Render build step: fetch the pre-built FAA sectional tile pyramid (GitHub Release asset named in tools/chart-release.txt)
# into public/tiles. Never fails the build: without tiles the page still shows public/chart.jpg (full view).
set -u; cd "$(dirname "$0")/.."
[ -d public/tiles/4 ] && { echo "tiles already present"; exit 0; }
U=$(tr -d ' \n' < tools/chart-release.txt)
echo "tiles: $U"
curl -sSL --retry 4 -m 900 "$U" | tar -x -C public && echo "tiles ok: $(find public/tiles -name '*.webp' | wc -l)" || echo "tile download failed (full-view chart.jpg still works)"
exit 0
