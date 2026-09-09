#!/usr/bin/env python3
"""
make_gis_workspace.py — build the GIS workspace for the Anantapur hydrology study.

Produces:
  hydrology_study.gpkg   an OGC GeoPackage holding every study layer, empty but
                         fully schema'd, so field names and types are fixed before
                         any data is collected.
  hydrology_study.qgz    a QGIS project that loads those layers, styled, with the
                         project CRS set to the local UTM zone for metric work.

The GeoPackage is written directly against the OGC GeoPackage 1.3 spec using the
standard library only (a .gpkg is a SQLite database with prescribed metadata
tables). It is then validated by reading it back through GDAL.

Layer geometry is stored in EPSG:4326, because that is how boundary and GPS data
arrives. The QGIS *project* CRS is EPSG:32643 (WGS 84 / UTM 43N) so that lengths,
areas and buffers are computed in metres. QGIS reprojects on the fly.
"""

import os
import shutil
import sqlite3
import zipfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
GPKG = "hydrology_study.gpkg"
QGZ = "hydrology_study.qgz"

# UTM zone 43N covers 72E-78E, which is where Anantapur sits. Confirm against the
# real boundary once it arrives (boundary_kml.py prints the zone).
PROJECT_SRS_ID = 32643
PROJECT_SRS_NAME = "WGS 84 / UTM zone 43N"

WKT_4326 = (
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,'
    'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],'
    'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],'
    'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
    'AUTHORITY["EPSG","4326"]]'
)
WKT_32643 = (
    'PROJCS["WGS 84 / UTM zone 43N",' + WKT_4326.replace('GEOGCS["WGS 84"', 'GEOGCS["WGS 84"', 1)
    + ',PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],'
    'PARAMETER["central_meridian",75],PARAMETER["scale_factor",0.9996],'
    'PARAMETER["false_easting",500000],PARAMETER["false_northing",0],'
    'UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],'
    'AXIS["Northing",NORTH],AUTHORITY["EPSG","32643"]]'
)

# ---------------------------------------------------------------------------
# Layer definitions. Field names deliberately match the deliverables in the
# proposal (D1a, D4, D6, D8) so the report tables and the GIS agree.
# ---------------------------------------------------------------------------
LAYERS = [
    ("boundary", "POLYGON", "Project boundary as notified by the Client (D1a)", [
        ("name", "TEXT"), ("source", "TEXT"), ("received_on", "TEXT"),
        ("gross_area_sqkm", "REAL"), ("excluded_sqkm", "REAL"),
        ("net_area_sqkm", "REAL"), ("net_area_ha", "REAL"), ("net_area_acres", "REAL"),
        ("perimeter_km", "REAL"), ("datum", "TEXT"), ("notes", "TEXT"),
    ]),
    ("external_catchments", "POLYGON",
     "Catchments draining INTO the site from outside the boundary (D4)", [
        ("catch_id", "TEXT"), ("name", "TEXT"), ("area_sqkm", "REAL"),
        ("outlet_node", "TEXT"), ("tc_min", "REAL"), ("cn_amc2", "REAL"),
        ("cn_amc3", "REAL"), ("mean_slope_pct", "REAL"), ("notes", "TEXT"),
     ]),
    ("sub_catchments", "POLYGON", "Internal sub-catchments at each drainage node (D4)", [
        ("catch_id", "TEXT"), ("name", "TEXT"), ("area_sqkm", "REAL"),
        ("outlet_node", "TEXT"), ("longest_path_m", "REAL"), ("tc_min", "REAL"),
        ("cn_amc2", "REAL"), ("cn_amc3", "REAL"), ("mean_slope_pct", "REAL"),
        ("hsg", "TEXT"), ("notes", "TEXT"),
    ]),
    ("drainage_lines", "LINESTRING", "Natural stream and vanka network (D4)", [
        ("reach_id", "TEXT"), ("name", "TEXT"), ("stream_order", "INTEGER"),
        ("length_m", "REAL"), ("bed_width_m", "REAL"), ("regime", "TEXT"),
        ("bed_slope_pct", "REAL"), ("notes", "TEXT"),
    ]),
    ("tanks", "POLYGON",
     "Minor-irrigation tanks and cascade. FTL/MWL govern siting - see Section 2.2", [
        ("tank_id", "TEXT"), ("name", "TEXT"), ("cascade_id", "TEXT"),
        ("ftl_m", "REAL"), ("mwl_m", "REAL"), ("tbl_m", "REAL"),
        ("ayacut_ha", "REAL"), ("capacity_mcum", "REAL"),
        ("surplus_route", "TEXT"), ("position", "TEXT"), ("breach_risk", "TEXT"),
        ("source", "TEXT"), ("notes", "TEXT"),
     ]),
    ("tank_channels", "LINESTRING", "Tank feeder and surplus channels (D4)", [
        ("channel_id", "TEXT"), ("tank_id", "TEXT"), ("channel_type", "TEXT"),
        ("length_m", "REAL"), ("capacity_cumec", "REAL"), ("notes", "TEXT"),
    ]),
    ("roads", "LINESTRING", "Proposed internal road network and village bypasses (D8)", [
        ("road_id", "TEXT"), ("road_class", "TEXT"), ("length_m", "REAL"),
        ("pavement_type", "TEXT"), ("subgrade_treatment", "TEXT"),
        ("min_formation_rl", "REAL"), ("camber_pct", "REAL"),
        ("return_period_yr", "INTEGER"), ("notes", "TEXT"),
    ]),
    ("drains", "LINESTRING", "Side, mitre, catch-water and cut-off drains (D8)", [
        ("drain_id", "TEXT"), ("drain_type", "TEXT"), ("lining", "TEXT"),
        ("length_m", "REAL"), ("section", "TEXT"), ("design_q_cumec", "REAL"),
        ("gradient_pct", "REAL"), ("velocity_ms", "REAL"),
        ("return_period_yr", "INTEGER"), ("outfall_to", "TEXT"), ("notes", "TEXT"),
    ]),
    ("crossings", "POINT",
     "Cross-drainage structure schedule - one row per crossing (D8)", [
        ("xing_id", "TEXT"), ("road_id", "TEXT"), ("catchment_area_sqkm", "REAL"),
        ("return_period_yr", "INTEGER"), ("design_q_cumec", "REAL"),
        ("q_with_cc_cumec", "REAL"), ("structure_type", "TEXT"),
        ("vent_size", "TEXT"), ("vent_count", "INTEGER"),
        ("invert_rl", "REAL"), ("soffit_rl", "REAL"), ("hfl_rl", "REAL"),
        ("afflux_m", "REAL"), ("outlet_vel_ms", "REAL"), ("scour_depth_m", "REAL"),
        ("found_depth_m", "REAL"), ("protection", "TEXT"),
        ("blockage_check", "TEXT"), ("notes", "TEXT"),
     ]),
    ("existing_structures", "POINT",
     "Inventory and condition of existing culverts, causeways, sluices (D2)", [
        ("struct_id", "TEXT"), ("struct_type", "TEXT"), ("dimensions", "TEXT"),
        ("invert_rl", "REAL"), ("condition", "TEXT"), ("blockage", "TEXT"),
        ("surveyed_on", "TEXT"), ("photo_ref", "TEXT"), ("notes", "TEXT"),
     ]),
    ("soil_points", "POINT", "Soil investigation locations and results (D3)", [
        ("point_id", "TEXT"), ("trial_pit_depth_m", "REAL"), ("bc_soil_depth_m", "REAL"),
        ("liquid_limit", "REAL"), ("plastic_limit", "REAL"), ("plasticity_index", "REAL"),
        ("free_swell_index", "REAL"), ("swell_pressure_kpa", "REAL"),
        ("cbr_soaked_pct", "REAL"), ("cbr_unsoaked_pct", "REAL"),
        ("infiltration_mm_hr", "REAL"), ("gwt_premonsoon_m", "REAL"),
        ("gwt_postmonsoon_m", "REAL"), ("hsg", "TEXT"), ("sampled_on", "TEXT"),
    ]),
    ("constraint_zones", "POLYGON",
     "Zone A unsuitable / B conditional / C suitable - the key output (D8, 6.8.1)", [
        ("zone", "TEXT"), ("reason", "TEXT"), ("min_platform_rl", "REAL"),
        ("hazard_rating", "TEXT"), ("max_depth_m", "REAL"),
        ("max_velocity_ms", "REAL"), ("ponding_hours", "REAL"),
        ("return_period_yr", "INTEGER"), ("mitigation", "TEXT"),
     ]),
    ("flood_extent", "POLYGON", "Modelled flood extent by return period (D6)", [
        ("return_period_yr", "INTEGER"), ("scenario", "TEXT"),
        ("climate_uplift", "TEXT"), ("max_depth_m", "REAL"),
        ("max_velocity_ms", "REAL"), ("ponding_hours", "REAL"), ("run_id", "TEXT"),
    ]),
    ("wtg_candidates", "POINT",
     "WTG positions tested against the constraint surface. Tentative - see Section 1", [
        ("wtg_id", "TEXT"), ("layout_rev", "TEXT"), ("ground_rl", "REAL"),
        ("min_platform_rl", "REAL"), ("zone", "TEXT"), ("verdict", "TEXT"),
        ("mitigation", "TEXT"), ("checked_on", "TEXT"),
     ]),
    ("survey_control", "POINT", "DGPS ground control and check points (D2)", [
        ("station_id", "TEXT"), ("station_type", "TEXT"), ("easting", "REAL"),
        ("northing", "REAL"), ("elevation_m", "REAL"), ("utm_zone", "TEXT"),
        ("h_accuracy_m", "REAL"), ("v_accuracy_m", "REAL"), ("established_on", "TEXT"),
    ]),
    ("erosion_features", "POLYGON", "Gullies, rills and active erosion (D7)", [
        ("feature_id", "TEXT"), ("feature_type", "TEXT"), ("area_sqm", "REAL"),
        ("depth_m", "REAL"), ("activity", "TEXT"), ("soil_loss_t_ha_yr", "REAL"),
        ("treatment", "TEXT"),
    ]),
    ("observations", "POINT",
     "Reconnaissance and community flood evidence - georeferenced (D1, 6.1)", [
        ("obs_id", "TEXT"), ("obs_type", "TEXT"), ("description", "TEXT"),
        ("informant", "TEXT"), ("event_date", "TEXT"), ("observed_depth_m", "REAL"),
        ("access_lost_days", "REAL"), ("photo_ref", "TEXT"), ("recorded_on", "TEXT"),
     ]),
]

GEOM_QGIS = {"POINT": "Point", "LINESTRING": "Line", "POLYGON": "Polygon"}

# fill, stroke, width  (QGIS colour strings are "r,g,b,a")
STYLE = {
    "boundary":            ("255,80,255,50",  "255,0,255,255",   "0.86"),
    "constraint_zones":    ("227,26,28,90",   "177,0,38,255",    "0.4"),
    "flood_extent":        ("49,130,189,90",  "8,81,156,255",    "0.26"),
    "tanks":               ("116,196,255,120","8,81,156,255",    "0.4"),
    "external_catchments": ("255,255,255,0",  "140,81,10,255",   "0.6"),
    "sub_catchments":      ("255,255,255,0",  "191,129,45,255",  "0.36"),
    "erosion_features":    ("217,95,14,110",  "140,45,4,255",    "0.3"),
    "drainage_lines":      (None,             "33,113,181,255",  "0.56"),
    "tank_channels":       (None,             "107,174,214,255", "0.4"),
    "roads":               (None,             "35,35,35,255",    "0.66"),
    "drains":              (None,             "0,160,120,255",   "0.4"),
    "crossings":           ("255,127,0,255",  "80,40,0,255",     "0.4"),
    "existing_structures": ("150,150,150,255", "60,60,60,255",   "0.4"),
    "soil_points":         ("140,81,10,255",  "60,30,0,255",     "0.4"),
    "wtg_candidates":      ("44,162,95,255",  "0,68,27,255",     "0.4"),
    "survey_control":      ("255,237,111,255","120,100,0,255",   "0.4"),
    "observations":        ("152,78,163,255", "60,20,80,255",    "0.4"),
}


# ---------------------------------------------------------------------------
def build_gpkg(path):
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("PRAGMA application_id = 1196444487")   # 'GPKG'
    cur.execute("PRAGMA user_version = 10300")          # GeoPackage 1.3

    cur.execute("""CREATE TABLE gpkg_spatial_ref_sys (
        srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY,
        organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL,
        definition TEXT NOT NULL, description TEXT)""")
    cur.executemany(
        "INSERT INTO gpkg_spatial_ref_sys VALUES (?,?,?,?,?,?)", [
            ("Undefined cartesian SRS", -1, "NONE", -1, "undefined", None),
            ("Undefined geographic SRS", 0, "NONE", 0, "undefined", None),
            ("WGS 84 geodetic", 4326, "EPSG", 4326, WKT_4326, "longitude/latitude"),
            (PROJECT_SRS_NAME, PROJECT_SRS_ID, "EPSG", PROJECT_SRS_ID, WKT_32643,
             "metric working CRS"),
        ])

    cur.execute("""CREATE TABLE gpkg_contents (
        table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL,
        identifier TEXT UNIQUE, description TEXT DEFAULT '',
        last_change DATETIME NOT NULL
            DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER,
        CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id)
            REFERENCES gpkg_spatial_ref_sys(srs_id))""")

    cur.execute("""CREATE TABLE gpkg_geometry_columns (
        table_name TEXT NOT NULL, column_name TEXT NOT NULL,
        geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL,
        z TINYINT NOT NULL, m TINYINT NOT NULL,
        CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),
        CONSTRAINT uk_gc_table_name UNIQUE (table_name),
        CONSTRAINT fk_gc_tn FOREIGN KEY (table_name)
            REFERENCES gpkg_contents(table_name),
        CONSTRAINT fk_gc_srs FOREIGN KEY (srs_id)
            REFERENCES gpkg_spatial_ref_sys (srs_id))""")

    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    for tbl, geom, desc, fields in LAYERS:
        cols = ",\n  ".join(f'"{n}" {t}' for n, t in fields)
        cur.execute(f'''CREATE TABLE "{tbl}" (
  fid INTEGER PRIMARY KEY AUTOINCREMENT,
  geom {geom},
  {cols})''')
        cur.execute("INSERT INTO gpkg_contents (table_name, data_type, identifier,"
                    " description, last_change, srs_id) VALUES (?,?,?,?,?,?)",
                    (tbl, "features", tbl, desc, now, 4326))
        cur.execute("INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?,?,?)",
                    (tbl, "geom", geom, 4326, 0, 0))

    con.commit()
    con.close()


# ---------------------------------------------------------------------------
def symbol_xml(name, geom):
    fill, stroke, width = STYLE.get(name, ("200,200,200,150", "80,80,80,255", "0.4"))
    if geom == "POLYGON":
        return f'''<symbol type="fill" name="0" alpha="1" clip_to_extent="1" force_rhr="0" frame_rate="10">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="color" type="QString" value="{fill}"/>
            <Option name="outline_color" type="QString" value="{stroke}"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="{width}"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
          </Option>
        </layer>
      </symbol>'''
    if geom == "LINESTRING":
        return f'''<symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0" frame_rate="10">
        <layer class="SimpleLine" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="line_color" type="QString" value="{stroke}"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="line_width" type="QString" value="{width}"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="capstyle" type="QString" value="round"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>'''
    return f'''<symbol type="marker" name="0" alpha="1" clip_to_extent="1" force_rhr="0" frame_rate="10">
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="{fill}"/>
            <Option name="outline_color" type="QString" value="{stroke}"/>
            <Option name="outline_width" type="QString" value="{width}"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="2.6"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>'''


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def srs_block(srsid, wkt, name, proj4, geographic):
    return f'''<spatialrefsys nativeFormat="Wkt">
      <wkt>{esc(wkt)}</wkt>
      <proj4>{esc(proj4)}</proj4>
      <srsid>{srsid}</srsid>
      <srid>{srsid}</srid>
      <authid>EPSG:{srsid}</authid>
      <description>{esc(name)}</description>
      <projectionacronym>{"longlat" if geographic else "utm"}</projectionacronym>
      <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
      <geographicflag>{"true" if geographic else "false"}</geographicflag>
    </spatialrefsys>'''


SRS_4326 = srs_block(4326, WKT_4326, "WGS 84",
                     "+proj=longlat +datum=WGS84 +no_defs", True)
SRS_PROJ = srs_block(PROJECT_SRS_ID, WKT_32643, PROJECT_SRS_NAME,
                     "+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs", False)


def build_qgs(gpkg_name):
    tree, layers = [], []
    for tbl, geom, desc, fields in LAYERS:
        lid = f"{tbl}_layer"
        src = f"./{gpkg_name}|layername={tbl}"
        # boundary and constraint zones on top and visible; the rest off by default
        checked = "Qt::Checked" if tbl in (
            "boundary", "constraint_zones", "tanks", "drainage_lines") else "Qt::Unchecked"
        tree.append(f'<layer-tree-layer id="{lid}" name="{tbl}" source="{esc(src)}" '
                    f'providerKey="ogr" checked="{checked}" expanded="0" '
                    f'legend_exp="" legend_split_behavior="0"><customproperties>'
                    f'<Option/></customproperties></layer-tree-layer>')
        layers.append(f'''<maplayer type="vector" geometry="{GEOM_QGIS[geom]}"
        hasScaleBasedVisibilityFlag="0" minScale="1e+08" maxScale="0"
        simplifyDrawingHints="1" simplifyDrawingTol="1" simplifyMaxScale="1"
        simplifyLocal="1" simplifyAlgorithm="0" readOnly="0" refreshOnNotifyEnabled="0"
        autoRefreshMode="Disabled" styleCategories="AllStyleCategories">
      <id>{lid}</id>
      <datasource>{esc(src)}</datasource>
      <layername>{esc(tbl)}</layername>
      <srs>{SRS_4326}</srs>
      <provider encoding="UTF-8">ogr</provider>
      <abstract>{esc(desc)}</abstract>
      <keywordList><value></value></keywordList>
      <renderer-v2 type="singleSymbol" symbollevels="0" forceraster="0"
                   enableorderby="0" referencescale="-1">
        <symbols>{symbol_xml(tbl, geom)}</symbols>
      </renderer-v2>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
    </maplayer>''')

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<qgis projectname="Anantapur Wind - Hydrology Study" version="3.34.0-Prizren" saveDateTime="">
  <homePath path=""/>
  <title>Anantapur Wind - Hydrology Study</title>
  <autotransaction active="0"/>
  <evaluateDefaultValues active="0"/>
  <trust active="0"/>
  <projectCrs>{SRS_PROJ}</projectCrs>
  <layer-tree-group>
    {"".join(tree)}
    <custom-order enabled="0"/>
  </layer-tree-group>
  <snapping-settings enabled="0" type="1" mode="2" tolerance="12" unit="1"
                     intersection-snapping="0" self-snapping="0"/>
  <relations/>
  <mapcanvas name="theMapCanvas" annotationsVisible="1">
    <units>meters</units>
    <destinationsrs>{SRS_PROJ}</destinationsrs>
    <rotation>0</rotation>
  </mapcanvas>
  <projectModels/>
  <legend updateDrawingOrder="true"/>
  <mapViewDocks/>
  <projectlayers>
    {"".join(layers)}
  </projectlayers>
  <layerorder/>
  <properties>
    <Measure><Ellipsoid type="QString">EPSG:7030</Ellipsoid></Measure>
    <Measurement>
      <AreaUnits type="QString">m2</AreaUnits>
      <DistanceUnits type="QString">meters</DistanceUnits>
    </Measurement>
    <PositionPrecision>
      <Automatic type="bool">true</Automatic>
    </PositionPrecision>
  </properties>
  <visibility-presets/>
  <transaction mode="Disabled"/>
  <projectFlags set=""/>
</qgis>
'''


def main():
    out = os.path.join(HERE, "gis_workspace")
    os.makedirs(out, exist_ok=True)
    gpkg_path = os.path.join(out, GPKG)
    build_gpkg(gpkg_path)

    qgs = build_qgs(GPKG)
    qgs_name = "hydrology_study.qgs"
    qgz_path = os.path.join(out, QGZ)
    if os.path.exists(qgz_path):
        os.remove(qgz_path)
    with zipfile.ZipFile(qgz_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(qgs_name, qgs)

    print(f"GeoPackage : {gpkg_path}")
    print(f"QGIS project: {qgz_path}")
    print(f"Layers      : {len(LAYERS)}")


if __name__ == "__main__":
    main()
