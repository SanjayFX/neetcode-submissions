#!/usr/bin/env python3
"""
boundary_kml.py — Project boundary -> Google Earth KML + area schedule.

Takes a wind-farm (or any) project boundary from KML / KMZ / GeoJSON / a plain
coordinate list, and produces:

  1. <out>.kml  — a styled, Google Earth-ready boundary file (pink, semi-transparent,
                  labelled, with area details embedded as ExtendedData).
  2. <out>_area.csv  — per-polygon area schedule.
  3. <out>_area.md   — the same schedule as a report-ready table.
  4. A printed summary: total area (sq km / ha / acres), perimeter, centroid,
     bounding box, extents, and the local UTM zone.

Areas are computed on the WGS84 ellipsoid using an oblique Lambert Azimuthal
Equal-Area projection centred on the polygon (Snyder, Map Projections - A Working
Manual, USGS PP1395). That projection preserves area exactly, so the planar
shoelace area of the projected ring IS the true ellipsoidal area. A spherical
excess calculation is run alongside as an independent cross-check; the two are
reported together so any disagreement is visible rather than hidden.

Pure standard library. No numpy, shapely, pyproj or GDAL required.

Usage
-----
    python3 boundary_kml.py boundary.kml
    python3 boundary_kml.py boundary.kmz  -o anantapur_boundary --name "Wind Farm Boundary"
    python3 boundary_kml.py coords.csv    --latlon       # file of "lat,lon" lines
    python3 boundary_kml.py coords.csv    --lonlat       # file of "lon,lat" lines
    python3 boundary_kml.py boundary.geojson

Options
-------
    -o, --out NAME     output basename            (default: derived from input)
    --name TEXT        boundary label in Google Earth
    --colour AABBGGRR  KML colour override (KML uses AABBGGRR, not RRGGBB)
    --latlon/--lonlat  axis order for plain text input (default: auto-detect)
"""

import argparse
import csv
import json
import math
import os
import re
import sys
import sqlite3
import struct
import zipfile
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- WGS84
A = 6378137.0                      # semi-major axis, m
F = 1.0 / 298.257223563            # flattening
E2 = F * (2 - F)                   # first eccentricity squared
E = math.sqrt(E2)
B_AXIS = A * (1 - F)

SQKM = 1e6
HECTARE = 1e4
ACRE = 4046.8564224


# ---------------------------------------------------------------- geodesy
def _q(phi):
    """Snyder eq. 3-12: the authalic-area function q(phi)."""
    s = math.sin(phi)
    if abs(s) < 1e-15:
        return 0.0
    return (1 - E2) * (
        s / (1 - E2 * s * s)
        - (1.0 / (2 * E)) * math.log((1 - E * s) / (1 + E * s))
    )


_QP = _q(math.pi / 2)
_RQ = A * math.sqrt(_QP / 2.0)      # radius of the authalic sphere


def laea_forward(lat, lon, lat0, lon0):
    """Oblique Lambert Azimuthal Equal-Area, ellipsoidal (Snyder 24-x).

    Returns planar (x, y) in metres. Area is preserved exactly.
    """
    phi, lam = math.radians(lat), math.radians(lon)
    phi0, lam0 = math.radians(lat0), math.radians(lon0)

    beta = math.asin(max(-1.0, min(1.0, _q(phi) / _QP)))
    beta0 = math.asin(max(-1.0, min(1.0, _q(phi0) / _QP)))
    m0 = math.cos(phi0) / math.sqrt(1 - E2 * math.sin(phi0) ** 2)

    dlam = lam - lam0
    denom = 1 + math.sin(beta0) * math.sin(beta) + \
        math.cos(beta0) * math.cos(beta) * math.cos(dlam)
    denom = max(denom, 1e-15)
    B = _RQ * math.sqrt(2.0 / denom)
    D = A * m0 / (_RQ * math.cos(beta0))

    x = B * D * math.cos(beta) * math.sin(dlam)
    y = (B / D) * (math.cos(beta0) * math.sin(beta)
                   - math.sin(beta0) * math.cos(beta) * math.cos(dlam))
    return x, y


def shoelace(pts):
    """Signed planar area (m^2). Positive = counter-clockwise."""
    n = len(pts)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def ellipsoidal_area(ring, lat0, lon0):
    """True ellipsoidal area of a lat/lon ring, in m^2."""
    proj = [laea_forward(la, lo, lat0, lon0) for la, lo in ring]
    return abs(shoelace(proj))


def _authalic_lat(lat):
    """Geodetic -> authalic latitude (radians in, radians out).

    Required before any spherical-area formula: feeding geodetic latitude
    straight into one biases the result by roughly 0.3-0.4% at these latitudes.
    """
    return math.asin(max(-1.0, min(1.0, _q(lat) / _QP)))


def spherical_excess_area(ring):
    """Independent cross-check on the area: Chamberlain & Duquette spherical
    excess, evaluated in authalic latitude on the WGS84 authalic sphere.

    This is a genuinely different route to the answer (spherical excess rather
    than a planar shoelace on a projected ring), so agreement between the two
    is meaningful evidence that neither has gone wrong."""
    R = A * math.sqrt(_QP / 2.0)          # authalic radius, m
    n = len(ring)
    if n < 3:
        return 0.0
    total = 0.0
    for i in range(n):
        la1, lo1 = ring[i]
        la2, lo2 = ring[(i + 1) % n]
        b1 = _authalic_lat(math.radians(la1))
        b2 = _authalic_lat(math.radians(la2))
        dlon = math.radians(lo2 - lo1)
        if dlon > math.pi:
            dlon -= 2 * math.pi
        elif dlon < -math.pi:
            dlon += 2 * math.pi
        total += dlon * (math.sin(b1) + math.sin(b2))
    return abs(total * R * R / 2.0)


def vincenty(lat1, lon1, lat2, lon2):
    """Vincenty inverse geodesic distance in metres (falls back to haversine)."""
    L = math.radians(lon2 - lon1)
    U1 = math.atan((1 - F) * math.tan(math.radians(lat1)))
    U2 = math.atan((1 - F) * math.tan(math.radians(lat2)))
    sU1, cU1 = math.sin(U1), math.cos(U1)
    sU2, cU2 = math.sin(U2), math.cos(U2)
    lam = L
    for _ in range(200):
        sl, cl = math.sin(lam), math.cos(lam)
        ss = math.sqrt((cU2 * sl) ** 2 + (cU1 * sU2 - sU1 * cU2 * cl) ** 2)
        if ss == 0:
            return 0.0
        cs = sU1 * sU2 + cU1 * cU2 * cl
        sigma = math.atan2(ss, cs)
        sa = cU1 * cU2 * sl / ss
        c2a = 1 - sa * sa
        c2sm = cs - 2 * sU1 * sU2 / c2a if c2a != 0 else 0.0
        C = F / 16 * c2a * (4 + F * (4 - 3 * c2a))
        lam_p = lam
        lam = L + (1 - C) * F * sa * (
            sigma + C * ss * (c2sm + C * cs * (-1 + 2 * c2sm ** 2)))
        if abs(lam - lam_p) < 1e-12:
            break
    else:
        # non-convergent (near-antipodal); haversine fallback
        dla = math.radians(lat2 - lat1)
        dlo = math.radians(lon2 - lon1)
        h = (math.sin(dla / 2) ** 2 + math.cos(math.radians(lat1))
             * math.cos(math.radians(lat2)) * math.sin(dlo / 2) ** 2)
        return 2 * 6371008.8 * math.asin(math.sqrt(h))

    u2 = c2a * (A * A - B_AXIS * B_AXIS) / (B_AXIS * B_AXIS)
    Aa = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    Bb = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    dsig = Bb * ss * (c2sm + Bb / 4 * (
        cs * (-1 + 2 * c2sm ** 2)
        - Bb / 6 * c2sm * (-3 + 4 * ss ** 2) * (-3 + 4 * c2sm ** 2)))
    return B_AXIS * Aa * (sigma - dsig)


def perimeter(ring):
    return sum(vincenty(ring[i][0], ring[i][1],
                        ring[(i + 1) % len(ring)][0], ring[(i + 1) % len(ring)][1])
               for i in range(len(ring)))


def utm_zone(lat, lon):
    z = int((lon + 180) / 6) + 1
    return f"{z}{'N' if lat >= 0 else 'S'}", 32600 + z if lat >= 0 else 32700 + z


# ---------------------------------------------------------------- parsing
def _coords(text):
    """Parse a KML <coordinates> blob -> [(lat, lon), ...]."""
    out = []
    for tok in text.replace("\n", " ").replace("\t", " ").split():
        parts = tok.split(",")
        if len(parts) >= 2:
            try:
                lon, lat = float(parts[0]), float(parts[1])
            except ValueError:
                continue
            out.append((lat, lon))
    return out


def _dedupe_closing(ring):
    """Drop a duplicated closing vertex; rings are treated as implicitly closed."""
    if len(ring) > 2 and abs(ring[0][0] - ring[-1][0]) < 1e-12 \
            and abs(ring[0][1] - ring[-1][1]) < 1e-12:
        return ring[:-1]
    return ring


def parse_kml(data):
    """-> [ {name, outer:[ring], inners:[ring,...]} ]"""
    txt = data.decode("utf-8", "replace") if isinstance(data, bytes) else data
    txt = re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", txt, count=0)   # strip namespaces
    root = ET.fromstring(txt)
    polys = []

    def ring_of(elem, tag):
        node = elem.find(f".//{tag}//coordinates")
        return _dedupe_closing(_coords(node.text)) if node is not None and node.text else None

    for pm in root.iter("Placemark"):
        nm = pm.findtext("name") or ""
        for poly in pm.iter("Polygon"):
            outer = ring_of(poly, "outerBoundaryIs")
            if not outer or len(outer) < 3:
                continue
            inners = []
            for ib in poly.iter("innerBoundaryIs"):
                c = ib.find(".//coordinates")
                if c is not None and c.text:
                    r = _dedupe_closing(_coords(c.text))
                    if len(r) >= 3:
                        inners.append(r)
            polys.append({"name": nm, "outer": outer, "inners": inners})

    if not polys:   # tolerate a bare LinearRing / LineString boundary
        for tag in ("LinearRing", "LineString"):
            for el in root.iter(tag):
                c = el.find("coordinates")
                if c is not None and c.text:
                    r = _dedupe_closing(_coords(c.text))
                    if len(r) >= 3:
                        polys.append({"name": "", "outer": r, "inners": []})
    return polys


def parse_kmz(path):
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".kml")]
        if not names:
            raise SystemExit("No .kml found inside the .kmz archive.")
        pref = [n for n in names if n.lower() == "doc.kml"] or names
        return parse_kml(z.read(pref[0]))


def parse_geojson(path):
    gj = json.load(open(path))
    feats = gj.get("features", [gj]) if gj.get("type") == "FeatureCollection" else [gj]
    polys = []
    for f in feats:
        geom = f.get("geometry", f)
        nm = (f.get("properties") or {}).get("name", "") or ""
        gt = geom.get("type")
        groups = [geom["coordinates"]] if gt == "Polygon" else \
                 (geom["coordinates"] if gt == "MultiPolygon" else [])
        for g in groups:
            rings = [_dedupe_closing([(c[1], c[0]) for c in r]) for r in g]
            if rings and len(rings[0]) >= 3:
                polys.append({"name": nm, "outer": rings[0], "inners": rings[1:]})
    return polys


# Matches 14°42'30.5"N  /  14 42 30.5 N  /  N 14d42m30s  /  14:42:30N
_DMS = re.compile(
    r"""(?P<pre>[NSEWnsew])?\s*
        (?P<d>\d{1,3}(?:\.\d+)?)\s*(?:[°dD:\s])\s*
        (?P<m>\d{1,2}(?:\.\d+)?)\s*(?:['\u2019mM:\s])\s*
        (?:(?P<s>\d{1,2}(?:\.\d+)?)\s*(?:["\u201dsS])?)?\s*
        (?P<post>[NSEWnsew])?""",
    re.VERBOSE)


def _dms_to_deg(m):
    """Convert one DMS regex match to signed decimal degrees, or None."""
    hemi = (m.group('pre') or m.group('post') or '').upper()
    if m.group('m') is None:
        return None
    deg = float(m.group('d')) + float(m.group('m')) / 60.0 \
        + (float(m.group('s')) / 3600.0 if m.group('s') else 0.0)
    if hemi in ('S', 'W'):
        deg = -deg
    return deg, hemi


def _parse_coord_line(line):
    """Pull one coordinate pair off a line of text.

    Handles decimal degrees and degrees/minutes/seconds in the forms commonly
    found in Indian survey and revenue records. Returns (a, b, hemis) or None.
    """
    line = line.strip()
    if not line or line.lstrip().startswith('#'):
        return None

    dms = [_dms_to_deg(m) for m in _DMS.finditer(line)]
    dms = [d for d in dms if d]
    if len(dms) >= 2:
        return dms[0][0], dms[1][0], (dms[0][1], dms[1][1])

    nums = re.findall(r'[-+]?\d+(?:\.\d+)?', line.replace(',', ' '))
    hemis = re.findall(r'(?<![A-Za-z])([NSEWnsew])(?![A-Za-z])', line)
    if len(nums) >= 2:
        a, b = float(nums[0]), float(nums[1])
        h = tuple(x.upper() for x in hemis[:2]) if len(hemis) >= 2 else ('', '')
        if h[0] in ('S',) or (h[0] == '' and False):
            a = -abs(a)
        if h[1] in ('W',):
            b = -abs(b)
        return a, b, h
    return None


def parse_text(path, order):
    """CSV / TXT of coordinate pairs, one per line. Decimal or DMS."""
    vals, hemis = [], []
    with open(path, newline='') as fh:
        for line in fh:
            got = _parse_coord_line(line)
            if got:
                vals.append((got[0], got[1]))
                hemis.append(got[2])
    if len(vals) < 3:
        raise SystemExit(
            f"Only {len(vals)} usable coordinate pair(s) found in {path}; need at least 3.\n"
            "Expected one coordinate per line, e.g.  14.708300, 77.504200\n"
            "or  14 42 29.9 N, 77 30 15.1 E")

    if order == 'auto':
        # An explicit N/S/E/W marker settles it outright.
        marked = [h for h in hemis if h[0] and h[1]]
        if marked and all(h[0] in 'NS' and h[1] in 'EW' for h in marked):
            order = 'latlon'
        elif marked and all(h[0] in 'EW' and h[1] in 'NS' for h in marked):
            order = 'lonlat'
        else:
            # Latitude is bounded by +/-90; longitude is not. If one column
            # strays outside that, the ambiguity resolves itself.
            c0 = [v[0] for v in vals]
            c1 = [v[1] for v in vals]
            if max(abs(x) for x in c0) > 90:
                order = 'lonlat'
            elif max(abs(x) for x in c1) > 90:
                order = 'latlon'
            else:
                order = 'latlon'
                print("  ! Axis order ambiguous - assuming lat,lon. "
                      "Re-run with --lonlat if the plotted shape looks wrong.",
                      file=sys.stderr)
    ring = vals if order == 'latlon' else [(b, a) for a, b in vals]
    return [{"name": "", "outer": _dedupe_closing(ring), "inners": []}]


def load(path, order):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".kml":
        return parse_kml(open(path, "rb").read())
    if ext == ".kmz":
        return parse_kmz(path)
    if ext in (".geojson", ".json"):
        return parse_geojson(path)
    if ext in (".csv", ".txt", ".tsv", ""):
        return parse_text(path, order)
    if ext == ".shp":
        raise SystemExit(
            "Shapefiles need a converter that is not installed here.\n"
            "Convert first (QGIS: Export > Save Features As > KML), or run:\n"
            "    ogr2ogr -f KML out.kml in.shp")
    raise SystemExit(f"Unsupported input type: {ext}")



# ---------------------------------------------------------------- GeoPackage
def _gpkg_polygon(outer, inners, srs=4326):
    """Encode a ring (plus holes) as a GeoPackageBinary blob."""
    def ring(r):
        b = struct.pack('<I', len(r) + 1)
        for la, lo in list(r) + [r[0]]:
            b += struct.pack('<dd', lo, la)      # WKB is x,y = lon,lat
        return b
    rings = [outer] + list(inners)
    wkb = struct.pack('<BI', 1, 3) + struct.pack('<I', len(rings))
    wkb += b"".join(ring(r) for r in rings)
    return b'GP' + bytes([0, 0b00000001]) + struct.pack('<i', srs) + wkb


def write_to_gpkg(path, polys, rows, lat0, lon0):
    """Insert the boundary into the study GeoPackage's `boundary` layer and
    refresh the layer extent recorded in gpkg_contents."""
    if not os.path.exists(path):
        raise SystemExit(f"GeoPackage not found: {path}")
    con = sqlite3.connect(path)
    try:
        con.execute("SELECT 1 FROM gpkg_contents WHERE table_name='boundary'").fetchone()
    except sqlite3.Error as e:
        con.close()
        raise SystemExit(f"{path} does not look like the study GeoPackage: {e}")

    con.execute("DELETE FROM boundary")           # boundary is authoritative, not additive
    today = __import__('datetime').date.today().isoformat()
    for poly, r in zip(polys, rows):
        con.execute(
            "INSERT INTO boundary (geom, name, source, received_on, gross_area_sqkm,"
            " excluded_sqkm, net_area_sqkm, net_area_ha, net_area_acres,"
            " perimeter_km, datum, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (_gpkg_polygon(poly["outer"], poly["inners"]), r["polygon"],
             os.path.basename(sys.argv[1]), today, r["gross_sqkm"],
             r["excluded_sqkm"], r["net_sqkm"], r["net_ha"], r["net_acres"],
             r["perimeter_km"], "WGS84 (EPSG:4326)",
             "Area on the WGS84 ellipsoid, Lambert Azimuthal Equal-Area"))

    pts = [p for poly in polys for p in poly["outer"]]
    con.execute("UPDATE gpkg_contents SET min_x=?, min_y=?, max_x=?, max_y=?,"
                " last_change=strftime('%Y-%m-%dT%H:%M:%fZ','now')"
                " WHERE table_name='boundary'",
                (min(p[1] for p in pts), min(p[0] for p in pts),
                 max(p[1] for p in pts), max(p[0] for p in pts)))
    con.commit()
    con.close()


# ---------------------------------------------------------------- KML out
KML_TMPL = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>{docname}</name>
  <description><![CDATA[{desc}]]></description>
  <Style id="boundary">
    <LineStyle><color>{line}</color><width>3.2</width></LineStyle>
    <PolyStyle><color>{fill}</color><fill>1</fill><outline>1</outline></PolyStyle>
  </Style>
  <Style id="label">
    <IconStyle><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle>
    <LabelStyle><scale>1.0</scale><color>{line}</color></LabelStyle>
  </Style>
{placemarks}
</Document>
</kml>
"""

PM_TMPL = """  <Placemark>
    <name>{name}</name>
    <styleUrl>#boundary</styleUrl>
    <ExtendedData>
{data}    </ExtendedData>
    <Polygon>
      <tessellate>1</tessellate>
      <outerBoundaryIs><LinearRing><coordinates>
{outer}
      </coordinates></LinearRing></outerBoundaryIs>
{inners}    </Polygon>
  </Placemark>
"""

INNER_TMPL = """      <innerBoundaryIs><LinearRing><coordinates>
{c}
      </coordinates></LinearRing></innerBoundaryIs>
"""

LABEL_TMPL = """  <Placemark>
    <name>{name}</name>
    <styleUrl>#label</styleUrl>
    <Point><coordinates>{lon:.8f},{lat:.8f},0</coordinates></Point>
  </Placemark>
"""


def coord_block(ring, indent="        "):
    closed = list(ring) + [ring[0]]
    return "\n".join(f"{indent}{lo:.8f},{la:.8f},0" for la, lo in closed)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="boundary file (.kml/.kmz/.geojson/.csv/.txt)")
    ap.add_argument("-o", "--out", help="output basename")
    ap.add_argument("--name", default="Project Boundary", help="boundary label")
    ap.add_argument("--colour", "--color", dest="colour",
                    help="KML fill colour as AABBGGRR (default: 40FF50FF, pink @ 25%%)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--latlon", dest="order", action="store_const", const="latlon")
    g.add_argument("--lonlat", dest="order", action="store_const", const="lonlat")
    ap.add_argument("--gpkg", metavar="PATH",
                    help="also load the boundary into this study GeoPackage "
                         "(replaces any existing boundary feature)")
    ap.set_defaults(order="auto")
    args = ap.parse_args()

    out = args.out or os.path.splitext(os.path.basename(args.input))[0] + "_boundary"
    fill = args.colour or "40FF50FF"          # AABBGGRR: 25% alpha, magenta/pink
    line = "FFFF50FF"

    polys = load(args.input, args.order)
    if not polys:
        raise SystemExit("No polygon boundary found in the input file.")

    # projection origin = mean of all vertices
    allpts = [p for poly in polys for p in poly["outer"]]
    lat0 = sum(p[0] for p in allpts) / len(allpts)
    lon0 = sum(p[1] for p in allpts) / len(allpts)

    rows, placemarks = [], []
    tot_net = tot_gross = tot_per = 0.0

    for i, poly in enumerate(polys, 1):
        nm = poly["name"] or (args.name if len(polys) == 1 else f"{args.name} {i}")
        gross = ellipsoidal_area(poly["outer"], lat0, lon0)
        holes = sum(ellipsoidal_area(r, lat0, lon0) for r in poly["inners"])
        net = gross - holes
        per = perimeter(poly["outer"])
        chk = spherical_excess_area(poly["outer"])
        dev = abs(chk - gross) / gross * 100 if gross else 0.0

        tot_net += net
        tot_gross += gross
        tot_per += per

        rows.append({
            "polygon": nm, "vertices": len(poly["outer"]), "holes": len(poly["inners"]),
            "gross_sqkm": gross / SQKM, "excluded_sqkm": holes / SQKM,
            "net_sqkm": net / SQKM, "net_ha": net / HECTARE, "net_acres": net / ACRE,
            "perimeter_km": per / 1000.0, "crosscheck_dev_pct": dev,
        })

        data = "".join(
            f'      <Data name="{k}"><value>{esc(v)}</value></Data>\n'
            for k, v in [
                ("Net area (sq km)", f"{net/SQKM:.4f}"),
                ("Net area (hectares)", f"{net/HECTARE:.2f}"),
                ("Net area (acres)", f"{net/ACRE:.2f}"),
                ("Perimeter (km)", f"{per/1000:.3f}"),
                ("Vertices", len(poly["outer"])),
                ("Datum", "WGS84 (EPSG:4326)"),
                ("Area method", "Ellipsoidal, Lambert Azimuthal Equal-Area"),
            ])
        inners = "".join(INNER_TMPL.format(c=coord_block(r)) for r in poly["inners"])
        placemarks.append(PM_TMPL.format(name=esc(nm), data=data,
                                         outer=coord_block(poly["outer"]),
                                         inners=inners))

    lats = [p[0] for p in allpts]
    lons = [p[1] for p in allpts]
    s, n, w, e = min(lats), max(lats), min(lons), max(lons)
    cen_lat, cen_lon = (s + n) / 2, (w + e) / 2
    ew = vincenty(cen_lat, w, cen_lat, e) / 1000.0
    ns = vincenty(s, cen_lon, n, cen_lon) / 1000.0
    zone, epsg = utm_zone(cen_lat, cen_lon)

    placemarks.append(LABEL_TMPL.format(
        name=esc(f"{args.name} — {tot_net/SQKM:.2f} sq km"), lat=cen_lat, lon=cen_lon))

    desc = (f"{args.name}<br/>Net area: {tot_net/SQKM:.4f} sq km "
            f"({tot_net/HECTARE:.2f} ha / {tot_net/ACRE:.2f} acres)<br/>"
            f"Perimeter: {tot_per/1000:.3f} km<br/>Datum: WGS84 (EPSG:4326)<br/>"
            f"Area computed on the WGS84 ellipsoid (Lambert Azimuthal Equal-Area).")

    with open(out + ".kml", "w") as fh:
        fh.write(KML_TMPL.format(docname=esc(args.name), desc=desc,
                                 fill=fill, line=line,
                                 placemarks="".join(placemarks)))

    with open(out + "_area.csv", "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        for r in rows:
            wtr.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v)
                          for k, v in r.items()})

    with open(out + "_area.md", "w") as fh:
        fh.write(f"# {args.name} — Area Schedule\n\n")
        fh.write("| Polygon | Vertices | Gross (sq km) | Excluded (sq km) | "
                 "Net (sq km) | Net (ha) | Net (acres) | Perimeter (km) |\n")
        fh.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
        for r in rows:
            fh.write(f"| {r['polygon']} | {r['vertices']} | {r['gross_sqkm']:.4f} | "
                     f"{r['excluded_sqkm']:.4f} | {r['net_sqkm']:.4f} | "
                     f"{r['net_ha']:.2f} | {r['net_acres']:.2f} | "
                     f"{r['perimeter_km']:.3f} |\n")
        if len(rows) > 1:
            fh.write(f"| **Total** | | **{tot_gross/SQKM:.4f}** | "
                     f"**{(tot_gross-tot_net)/SQKM:.4f}** | **{tot_net/SQKM:.4f}** | "
                     f"**{tot_net/HECTARE:.2f}** | **{tot_net/ACRE:.2f}** | "
                     f"**{tot_per/1000:.3f}** |\n")
        fh.write(f"\nDatum WGS84 (EPSG:4326). Areas computed on the ellipsoid by "
                 f"Lambert Azimuthal Equal-Area projection. Local UTM zone {zone} "
                 f"(EPSG:{epsg}).\n")

    W = 62
    print("=" * W)
    print(f" {args.name.upper()} — BOUNDARY & AREA SUMMARY")
    print("=" * W)
    print(f" Source file        : {args.input}")
    print(f" Polygons           : {len(polys)}"
          f"   (vertices: {sum(r['vertices'] for r in rows)})")
    print("-" * W)
    print(f" Net area           : {tot_net/SQKM:12.4f} sq km")
    print(f"                      {tot_net/HECTARE:12.2f} hectares")
    print(f"                      {tot_net/ACRE:12.2f} acres")
    if tot_gross - tot_net > 1.0:
        print(f" (gross {tot_gross/SQKM:.4f} sq km less "
              f"{(tot_gross-tot_net)/SQKM:.4f} sq km excluded)")
    print(f" Perimeter          : {tot_per/1000:12.3f} km")
    print("-" * W)
    print(f" Centroid (WGS84)   : {cen_lat:.6f} N, {cen_lon:.6f} E")
    print(f" Bounding box       : N {n:.6f}  S {s:.6f}")
    print(f"                      E {e:.6f}  W {w:.6f}")
    print(f" Extents            : {ew:.2f} km E-W  x  {ns:.2f} km N-S")
    print(f" Local UTM zone     : {zone}  (EPSG:{epsg})")
    mx = max(r["crosscheck_dev_pct"] for r in rows)
    print(f" Cross-check spread : {mx:.4f}%  (ellipsoidal vs spherical excess)")
    print("=" * W)
    if args.gpkg:
        write_to_gpkg(args.gpkg, polys, rows, lat0, lon0)
        print(f" Loaded into GeoPackage: {args.gpkg} (layer 'boundary')")
        print("=" * W)
    print(f" Written: {out}.kml")
    print(f"          {out}_area.csv")
    print(f"          {out}_area.md")
    print("=" * W)


if __name__ == "__main__":
    main()
