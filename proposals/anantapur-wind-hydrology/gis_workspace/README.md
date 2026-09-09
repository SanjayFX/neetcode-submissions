# GIS Workspace — Hydrology Study, Wind Project, Anantapur District

| File | What it is |
|---|---|
| `hydrology_study.qgz` | QGIS project. Open this. |
| `hydrology_study.gpkg` | OGC GeoPackage holding all 17 study layers — empty, but fully schema'd. |

Open `hydrology_study.qgz` in QGIS 3.x. The project loads all layers from the
GeoPackage beside it, so keep the two files **in the same folder**; the project
references the data by relative path and will move with them.

## Coordinate reference systems

- **Layer geometry is stored in EPSG:4326** (WGS 84 lat/lon), because that is how
  boundary files, GPS and Google Earth data arrive.
- **The project CRS is EPSG:32643** (WGS 84 / UTM zone 43N) so the measure tool,
  buffers, lengths and areas all work in **metres**. QGIS reprojects on the fly.

UTM 43N covers 72°E–78°E, which is where Anantapur sits. Confirm it against the
real boundary once it arrives — `boundary_kml.py` prints the correct zone. If the
site straddles 78°E it belongs in 44N (EPSG:32644); change it in
*Project ▸ Properties ▸ CRS*.

Do not trust QGIS's on-screen area readout for the contract area. Use the figure
from `boundary_kml.py`, which computes on the WGS84 ellipsoid by an equal-area
projection and cross-checks it by a second method.

## Layers

Field names match the deliverables in the proposal, so the report tables and the
GIS agree without translation.

| Layer | Geom | Purpose | Deliverable |
|---|---|---|---|
| `boundary` | Polygon | Project boundary as notified | D1a |
| `external_catchments` | Polygon | Catchments draining in from **outside** the boundary | D4 |
| `sub_catchments` | Polygon | Internal sub-catchments per drainage node | D4 |
| `drainage_lines` | Line | Natural stream / vanka network | D4 |
| `tanks` | Polygon | Minor-irrigation tanks — FTL, MWL, TBL, cascade | D4 |
| `tank_channels` | Line | Feeder and surplus channels | D4 |
| `roads` | Line | Internal network and village bypasses | D8 |
| `drains` | Line | Side, mitre, catch-water and cut-off drains | D8 |
| `crossings` | Point | Cross-drainage structure schedule | D8 |
| `existing_structures` | Point | Inventory of existing culverts/causeways | D2 |
| `soil_points` | Point | Trial pits, swell, soaked CBR, infiltration, GWT | D3 |
| `constraint_zones` | Polygon | **Zone A/B/C + minimum platform RL** | D8 (6.8.1) |
| `flood_extent` | Polygon | Modelled extent by return period and scenario | D6 |
| `wtg_candidates` | Point | Layouts tested against the constraint surface | D8 |
| `survey_control` | Point | DGPS control and check points | D2 |
| `erosion_features` | Polygon | Gullies, rills, active erosion | D7 |
| `observations` | Point | Reconnaissance and community flood evidence | D1 |

`boundary`, `constraint_zones`, `tanks` and `drainage_lines` are switched on by
default; the rest are loaded but unchecked, so the project opens clean.

## Loading the boundary

Once the boundary file arrives, one command fills in the boundary layer, computes
the area and writes the Google Earth KML:

```bash
python3 ../tools/boundary_kml.py <boundary file> \
        --name "Wind Farm Boundary" \
        --gpkg hydrology_study.gpkg
```

It accepts KML, KMZ, GeoJSON, or a plain list of corner coordinates in decimal
degrees or DMS. It replaces any existing boundary feature (the boundary is
authoritative, not additive), fills in gross/net area in km², ha and acres,
perimeter and datum, and updates the layer extent so QGIS zooms to it correctly.

## A note on spatial indexes

The layers carry no GeoPackage RTree index. That is deliberate: the tables are
empty, an index on an empty table buys nothing, and the spec's index triggers
depend on `ST_MinX`-family functions that are unavailable to plain `sqlite3`,
which would stop simple Python scripts from loading data into the file.

Once a layer holds real data, add one in QGIS via *Layer ▸ Properties ▸ Source ▸
Create spatial index*, or let GDAL/`ogr2ogr` do it on write.

## Rebuilding

`make_gis_workspace.py` regenerates both files from scratch. Edit the `LAYERS`
list there to add a layer or change a field, then re-run it. It overwrites, so
copy any populated GeoPackage aside first.
