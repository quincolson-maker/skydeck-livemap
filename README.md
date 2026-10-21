# SkyDeck Live Map
LED-style METAR flight-category wall map for a TV/kiosk. FAA VFR Wall Planning Chart background, live METARs (aviationweather.gov, 5 min), live NEXRAD radar toggle (IEM, R key / Enter / button), and flight plans by email or `/plan`.
- `/?all=1` shows every station; `/?radar=1` starts with radar on.
- Chart background built by the `build-chart` GitHub Action (FAA public domain).
- Email: send or forward plans to **firerelief+qclivemap@mail.grokbot.com** (an assistant routine POSTs them to `/api/inbound`).
- Optional alternative: `tools/gmail-forwarder.gs` (Google Apps Script relay from quin.colson+livemapskydeck@gmail.com).
