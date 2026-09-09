# Hydrology Study Proposal — Wind Project, Anantapur District, AP

## Contents

| File | What it is |
|---|---|
| `Hydrology_Proposal_Anantapur_Wind_R0.pdf` | **The issue copy** — 25 pages, for sending to the client. |
| `Hydrology_Proposal_Anantapur_Wind_R0.docx` | Editable source of the same document (~9,000 words, 19 tables). Rev R0. |
| `tools/build_proposal.js` | Generates the document. Edit rates/text here and re-run. |
| `tools/mkpdf.sh` | Two-pass build → .docx + .pdf with correct contents-page numbers. |
| `tools/toc.json` | Cached heading→page map used by the build. Regenerated automatically. |
| `tools/boundary_kml.py` | Boundary → Google Earth KML + area schedule. |
| `tools/test_geo.py` | Validation suite for the geodesy in `boundary_kml.py`. |
| `tools/BOUNDARY_TEMPLATE.csv` | Paste the boundary corner coordinates in here, then run the tool. |

## Before issuing the proposal

1. **Insert the two missing attachments' content.** The client referenced a Scope of
   Work / Methodology / Reports document and a boundary map; neither was received.
   Reconcile Section 6 against their scope document before issue.
2. **Confirm the area.** Section 10 assumes an **80 sq km** boundary. Run
   `boundary_kml.py` on the real boundary and restate Parts B and D.
3. **Replace the rates.** All figures in Section 10 are indicative market rates,
   not a quotation. Substitute your own rate card.
4. **Fill the blank fields on the cover** — Prepared for, Prepared by, Proposal
   reference, Date of issue. These are deliberately left empty: the document
   carries no names anywhere, including in its metadata and page footer.
5. If you restructure the sections, re-run `mkpdf.sh` so the contents page renumbers.

## Regenerating the document

```bash
npm install docx                 # once
./tools/mkpdf.sh Hydrology_Proposal_Anantapur_Wind_R0
```

This produces both the .docx and the .pdf. It runs the build twice: the contents
page carries real page numbers, which are only knowable after the document has been
laid out, so the script renders, reads back where each heading landed, rebuilds, and
repeats until pagination stops moving.

Needs `libreoffice-writer` and `poppler-utils` for the PDF step
(`apt-get install -y libreoffice-writer poppler-utils`). Without them
`node tools/build_proposal.js out.docx` still produces the .docx on its own.

## boundary_kml.py

Turns a project boundary into a styled Google Earth KML plus a full area statement.
Pure standard library — no shapely/pyproj/GDAL needed.

```bash
python3 tools/boundary_kml.py boundary.kml  --name "Wind Farm Boundary"
python3 tools/boundary_kml.py boundary.kmz  -o anantapur
python3 tools/boundary_kml.py corners.csv   --latlon      # plain "lat,lon" lines
python3 tools/boundary_kml.py boundary.geojson
```

Accepts KML, KMZ, GeoJSON and plain coordinate lists. (For a shapefile, export to
KML from QGIS first, or `ogr2ogr -f KML out.kml in.shp`.)

If all you have is a list of corner coordinates, paste them into
`tools/BOUNDARY_TEMPLATE.csv` and run it on that. Decimal degrees and
degrees/minutes/seconds both work, in any of these forms:

```
14.708300, 77.504200
14 42 29.9 N, 77 30 15.1 E
14°42'29.9"N, 77°30'15.1"E
```

Axis order is auto-detected from N/S/E/W markers, or from any value outside
±90 (which can only be a longitude). If neither is present it assumes lat,lon
and says so — pass `--lonlat` to override.

Outputs:

* `<out>.kml` — styled pink boundary, labelled with area, area details embedded as
  ExtendedData, holes preserved. Opens directly in Google Earth.
* `<out>_area.csv` / `<out>_area.md` — per-polygon area schedule.
* Printed summary: net/gross area (sq km, ha, acres), perimeter, centroid,
  bounding box, N–S and E–W extents, local UTM zone.

### On the area figures

Areas are computed on the **WGS84 ellipsoid** via an oblique Lambert Azimuthal
Equal-Area projection centred on the polygon (Snyder, USGS PP1395). That projection
preserves area exactly, so the planar shoelace area of the projected ring *is* the
true ellipsoidal area — not an approximation. A spherical-excess calculation in
authalic latitude runs alongside as an independent cross-check, and the deviation
between the two is reported so any disagreement is visible rather than hidden.

`test_geo.py` checks the engine against analytically-exact ellipsoidal quadrangle
areas. Current status: agreement to **0.0000000%**, with both methods matching and
Vincenty distances matching a numerically-integrated meridian arc.

```bash
python3 tools/test_geo.py
```

Interior parcels (holes / exclusions) are subtracted, so gross and net area are
reported separately — which matters where tank poramboke or third-party parcels sit
inside the boundary.
