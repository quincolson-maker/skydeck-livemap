# SkyDeck Live Map
LED-style METAR flight-category wall map for a TV/kiosk. Live METARs (aviationweather.gov, 5 min), live NEXRAD radar toggle (IEM, R key / Enter / button), and flight plans by email or `/plan`.
- `/?all=1` shows every station; `/?radar=1` starts with radar on; `/?style=led` old glow markers.
- Zoom: mouse wheel / pinch / drag, `+` `-` keys, `0` resets. Deep link: `/?lat=37.06&lon=-88.77&zoom=40`.
- **Airport Spotlight** (only while a flight plan is loaded): map → departure → map → destination, every `?cycle=<seconds>` (default 10). Shows decoded METAR, TAF (nearest TAF within 40 NM if none issued, labelled), the FAA d-TPP airport diagram (current cycle, rendered with pdf.js) and USGS NAIP aerial imagery. Pauses 60 s after manual zoom/pan.
- Email: send or forward plans to **firerelief+qclivemap@mail.grokbot.com** (an assistant routine POSTs them to `/api/inbound`). Optional: `tools/gmail-forwarder.gs`.

## Chart
Background = **FAA VFR Sectional Aeronautical Charts**, GeoTIFFs downloaded directly from aeronav.faa.gov (public domain), 37 CONUS/border sheets
mosaicked into the app's Lambert Conformal Conic frame (`public/chart.json`, edition recorded there). Deep-zoom pyramid: 512 px WebP tiles, levels 0–4
(level 0 = 3840 px wide full view, level 4 = 61,440 px ≈ 77 m/px; FAA native is 42.3 m/px). The FAA no longer publishes the VFR Wall Planning Chart raster.
Tiles (~500 MB) live in a GitHub Release asset (`tools/chart-release.txt`) and are fetched by the Render build (`tools/build-chart.sh`), keeping the git repo small.

**Next FAA edition (56-day cycle):** `bash tools/update-chart.sh` (or `bash tools/update-chart.sh 10-29-2026`), then `git push` and redeploy.
Sheet clip polygons in `tools/sectional_clips.json` are from jlmcgraw/aviationCharts.
