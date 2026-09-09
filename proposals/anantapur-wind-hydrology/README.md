# Hydrology Study Proposal — Wind Project, Anantapur District, AP

## Contents

| File | What it is |
|---|---|
| `Hydrology_Proposal_Anantapur_Wind_R0.docx` | The techno-commercial proposal (~9,000 words, 19 tables). Rev R0, for internal review before issue. |
| `tools/build_proposal.js` | Generates the .docx. Edit rates/text here and re-run to regenerate cleanly. |
| `tools/boundary_kml.py` | Boundary → Google Earth KML + area schedule. |
| `tools/test_geo.py` | Validation suite for the geodesy in `boundary_kml.py`. |

## Before issuing the proposal

1. **Insert the two missing attachments' content.** The client referenced a Scope of
   Work / Methodology / Reports document and a boundary map; neither was received.
   Reconcile Section 6 against their scope document before issue.
2. **Confirm the area.** Section 10 assumes an **80 sq km** boundary. Run
   `boundary_kml.py` on the real boundary and restate Parts B and D.
3. **Replace the rates.** All figures in Section 10 are indicative market rates,
   not a quotation. Substitute your own rate card.
4. **Fill the placeholders** — `[Consultant name]`, `[Client name]`, `[REF/...]`, date.
5. Open in Word, right-click the Contents table → **Update Field** to populate page numbers.

## Regenerating the document

```bash
npm install docx
node tools/build_proposal.js Hydrology_Proposal_Anantapur_Wind_R0.docx
```

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
