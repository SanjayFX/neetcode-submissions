"""Build the multispectral windmill scope PDF."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak)

OUT = "."
PDF = f"{OUT}/Multispectral_Windmill_Scope.pdf"

ACCENT = colors.HexColor("#1a5276")
LIGHT = colors.HexColor("#d6eaf8")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("DocTitle", parent=styles["Title"], fontSize=22,
                          textColor=ACCENT, spaceAfter=6))
styles.add(ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11,
                          alignment=TA_CENTER, textColor=colors.HexColor("#555555")))
styles.add(ParagraphStyle("H1x", parent=styles["Heading1"], fontSize=15,
                          textColor=ACCENT, spaceBefore=14, spaceAfter=6))
styles.add(ParagraphStyle("H2x", parent=styles["Heading2"], fontSize=12,
                          textColor=ACCENT, spaceBefore=10, spaceAfter=4))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5,
                          leading=13, spaceAfter=4))
styles.add(ParagraphStyle("Bullet2", parent=styles["Normal"], fontSize=9.5,
                          leading=13, leftIndent=14, bulletIndent=4, spaceAfter=2))
styles.add(ParagraphStyle("Cap", parent=styles["Normal"], fontSize=8.5,
                          alignment=TA_CENTER, textColor=colors.HexColor("#666666"),
                          spaceBefore=3, spaceAfter=10))
styles.add(ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.5, leading=11))
styles.add(ParagraphStyle("CellH", parent=styles["Normal"], fontSize=9,
                          leading=11, textColor=colors.white, fontName="Helvetica-Bold"))


def P(text, style="Body"):
    return Paragraph(text, styles[style])


def B(text):
    return Paragraph(f"• {text}", styles["Bullet2"])


def make_table(header, rows, col_widths):
    data = [[Paragraph(h, styles["CellH"]) for h in header]]
    for r in rows:
        data.append([Paragraph(c, styles["Cell"]) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#aaaaaa")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


story = []

# ---------------- Title ----------------
story.append(Spacer(1, 0.8 * cm))
story.append(Paragraph("Multispectral Imagery for Wind Turbine (Windmill) Applications",
                       styles["DocTitle"]))
story.append(Paragraph("Project Scope Document — with Open-Source Technology Stack "
                       "and Sample Outputs", styles["Sub"]))
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph("Version 1.0 &nbsp;|&nbsp; 23 July 2026 &nbsp;|&nbsp; Status: Draft",
                       styles["Sub"]))
story.append(Spacer(1, 0.5 * cm))

# ---------------- 1. Purpose ----------------
story.append(P("1. Purpose &amp; Objectives", "H1x"))
story.append(P("This document defines the scope of a system that uses multispectral "
               "imagery (visible, red-edge, near-infrared and optionally SWIR/thermal "
               "bands) across the lifecycle of wind turbines: site selection, blade "
               "and structural inspection, environmental monitoring, and operations "
               "&amp; maintenance (O&amp;M) optimization. The solution is built "
               "entirely on open-source software."))
for b in [
    "Automate detection of blade defects (erosion, cracks, moisture ingress, lightning damage) from UAV multispectral captures.",
    "Produce site-analysis products (NDVI, land cover, soil/water masks) from open satellite data (Sentinel-2, Landsat).",
    "Track vegetation and environmental change around wind farms for permit compliance.",
    "Deliver georeferenced defect maps, severity classifications and inspection reports through an open-source GIS/web stack.",
]:
    story.append(B(b))

# ---------------- 2. Multispectral imagery in wind applications ----------------
story.append(P("2. Multispectral Imagery in Wind Applications", "H1x"))
story.append(P("Multispectral sensors capture reflectance in discrete bands beyond "
               "human vision — typically Blue, Green, Red, Red-Edge and Near-Infrared "
               "(400–1000 nm), optionally extended with SWIR and thermal-IR. Because "
               "materials such as composite gel coat, moisture, ice, corrosion, "
               "vegetation and bare soil each have distinct spectral signatures, "
               "band ratios and indices reveal conditions that ordinary RGB imagery "
               "misses. The main application areas across the wind energy lifecycle are:"))
story.append(make_table(
    ["Application Area", "What multispectral imagery provides"],
    [
        ["Blade inspection &amp; damage detection",
         "Cracks, leading-edge erosion, delamination, pitting and coating degradation; "
         "NIR/SWIR reveals moisture ingress and bonding defects under the gel coat; "
         "lightning-strike burn signatures; ice detection on blades for de-icing decisions."],
        ["Thermal &amp; structural health monitoring",
         "Combined with thermal-IR: hotspots in nacelle, gearbox, generator and electrical "
         "junctions; internal blade flaws via thermal gradients; corrosion on tower and flanges."],
        ["Site selection &amp; pre-construction survey",
         "Land cover / land use classification from Sentinel-2 or Landsat; soil moisture and "
         "terrain indicators for foundations and access roads; NDVI/EVI ecological baselines; "
         "surface roughness input to wind-flow modelling."],
        ["Environmental &amp; ecological monitoring",
         "Vegetation-health change detection around the farm; bird/bat habitat mapping for "
         "curtailment planning; erosion and drainage monitoring; periodic compliance reports."],
        ["Operations &amp; maintenance optimization",
         "Repeatable UAV fleet-wide blade scans with minimal downtime; spectral trend analysis "
         "for predictive maintenance; digital-twin integration; rapid post-storm triage."],
        ["Wake &amp; vegetation studies",
         "Vegetation stress patterns downstream of turbines (microclimate/wake effects); "
         "agricultural coexistence studies on leased land."],
        ["Offshore-specific applications",
         "Marine growth / biofouling on foundations; coating breakdown in the splash zone; "
         "sediment-plume monitoring during construction (phase 2)."],
    ],
    [4.6 * cm, 11.9 * cm]))
story.append(Spacer(1, 0.2 * cm))

# ---------------- 3. Scope ----------------
story.append(P("3. In-Scope Work Packages", "H1x"))
story.append(make_table(
    ["WP", "Work Package", "Description"],
    [
        ["WP1", "Data acquisition", "UAV multispectral flights (blade &amp; tower); ingest of Sentinel-2/Landsat scenes for site &amp; environment products."],
        ["WP2", "Preprocessing", "Radiometric calibration, band alignment/registration, orthorectification, mosaicking, reflectance conversion."],
        ["WP3", "Index &amp; analytics engine", "NDVI/NDRE/EVI computation, anomaly masks, change detection between inspection epochs."],
        ["WP4", "Defect detection (ML)", "CNN / classical CV models for crack, erosion, moisture and lightning-damage classification with severity grading."],
        ["WP5", "GIS &amp; reporting", "Georeferenced defect layers, web map dashboard, automated PDF inspection reports."],
        ["WP6", "O&amp;M integration", "Export to CMMS/digital-twin via open APIs; trend analysis across inspection cycles."],
    ],
    [1.3 * cm, 3.6 * cm, 11.6 * cm]))
story.append(Spacer(1, 0.25 * cm))
story.append(P("Out of scope (phase 1): SCADA data fusion, offshore marine-growth "
               "monitoring, real-time onboard (edge) inference, LiDAR integration.", "Body"))

# ---------------- 3. Open-source stack ----------------
story.append(P("4. Open-Source Software Stack", "H1x"))
story.append(make_table(
    ["Layer", "Tool (License)", "Role in this project"],
    [
        ["Satellite data access", "ESA Sentinel-2 / USGS Landsat (free &amp; open data); sentinelsat, pystac-client (GPL/Apache)", "Free multispectral scenes and API download for site &amp; environmental products."],
        ["Photogrammetry / stitching", "OpenDroneMap / WebODM (AGPL-3.0)", "Orthomosaics and 3D reconstruction from UAV multispectral flights, incl. band alignment for MicaSense-class sensors."],
        ["Raster / geospatial core", "GDAL (MIT), Rasterio (BSD), rioxarray (Apache-2.0)", "Reading, reprojecting, calibrating and writing multispectral rasters."],
        ["Scientific computing", "NumPy, SciPy, xarray (BSD)", "Band math: NDVI, NDRE, EVI, custom anomaly indices."],
        ["Image processing / CV", "OpenCV (Apache-2.0), scikit-image (BSD)", "Denoising, thresholding, morphology, contour extraction for defect masks."],
        ["Machine learning", "PyTorch (BSD) or TensorFlow (Apache-2.0); scikit-learn (BSD); Ultralytics YOLO (AGPL-3.0)", "Defect detection/classification models; random-forest land-cover classification."],
        ["Semantic segmentation", "segmentation-models-pytorch (MIT)", "U-Net/DeepLab blade-surface defect segmentation."],
        ["GIS desktop", "QGIS (GPL-2.0) + Semi-Automatic Classification Plugin", "Visual QA, manual labelling, land-cover classification workflows."],
        ["Spatial database", "PostGIS on PostgreSQL (GPL/PostgreSQL licenses)", "Storage of defect geometries, turbine assets, inspection epochs."],
        ["Web mapping / dashboard", "GeoServer (GPL-2.0), Leaflet (BSD), Streamlit (Apache-2.0)", "Serving tiles and interactive inspection dashboards."],
        ["Visualization / reports", "Matplotlib (PSF-based), ReportLab (BSD)", "Figures and automated PDF inspection reports (this document was produced with them)."],
        ["Workflow orchestration", "Apache Airflow (Apache-2.0)", "Scheduled ingestion, processing and report pipelines."],
    ],
    [3.0 * cm, 5.4 * cm, 8.1 * cm]))

# ---------------- 5. Datasets & formats ----------------
story.append(P("5. Drone (UAV) Platform &amp; Payload Sensor Requirements", "H1x"))
story.append(P("5.1 Minimum UAV platform requirements", "H2x"))
story.append(make_table(
    ["Requirement", "Minimum specification", "Why it matters"],
    [
        ["Airframe type", "Multirotor (quadcopter) with stabilized 3-axis gimbal",
         "Hovering and slow orbits around blades; steady captures in gusts."],
        ["Payload capacity", "&gt;= 350 g (integrated sensor) or &gt;= 900 g (M300/M350-class for external payloads)",
         "Must carry the multispectral sensor plus irradiance (DLS) module."],
        ["Flight endurance", "&gt;= 25–30 min per battery (with payload)",
         "One full blade (3 sides) or one site grid per battery swap."],
        ["Positioning", "RTK/PPK GNSS, 1–3 cm accuracy (base station or NTRIP)",
         "Repeatable, georeferenced captures for epoch-to-epoch change detection."],
        ["Wind tolerance", "&gt;= 12 m/s sustained",
         "Wind farm sites are windy by definition; inspection windows are short."],
        ["Obstacle sensing", "Omnidirectional avoidance + safety geofence",
         "Flying within 5–15 m of blades and tower."],
        ["Mission software", "Waypoint / orbit automation with terrain follow (open protocols: MAVLink preferred)",
         "Repeatable automated inspection paths; integration with OpenDroneMap outputs."],
        ["Regulatory", "Registered platform, remote-ID; pilot licensed per DGCA/FAA/EASA class",
         "Legal operation near tall structures."],
    ],
    [3.2 * cm, 6.6 * cm, 6.7 * cm]))

story.append(P("5.2 Payload sensor options (named) and minimum sensor specification", "H2x"))
story.append(make_table(
    ["Payload sensor (Name)", "Bands", "Resolution / GSD", "Notes"],
    [
        ["DJI Mavic 3M (Mavic 3 Multispectral) — integrated",
         "RGB + 4 MS bands (G 560, R 650, RE 730, NIR 860 nm)",
         "5 MP MS; ~5 cm/px @ 60 m",
         "Minimum-budget entry; RTK module included; sunlight sensor on top."],
        ["MicaSense RedEdge-P (external payload)",
         "5 MS bands (B, G, R, RedEdge, NIR) + panchro",
         "1.6 MP/band; ~2 cm/px @ 60 m (pan-sharpened)",
         "Industry standard for inspection; global shutter; DLS 2 irradiance sensor."],
        ["MicaSense Altum-PT (external payload)",
         "5 MS bands + panchro + thermal LWIR",
         "3.2 MP/band MS; 320x256 thermal",
         "Adds thermal for electrical/structural hotspots; heavier (577 g)."],
        ["Sentera 6X (external payload)",
         "5 MS bands + RGB",
         "3.2 MP/band",
         "Alternative vendor; global shutter; open SDK."],
        ["Parrot Sequoia+ (legacy option)",
         "4 MS bands + RGB",
         "1.2 MP/band",
         "Budget/legacy; acceptable for vegetation products only, not fine blade defects."],
    ],
    [4.2 * cm, 4.2 * cm, 3.7 * cm, 4.4 * cm]))
story.append(Spacer(1, 0.2 * cm))
story.append(P("<b>Minimum sensor specification for this project:</b> &gt;= 5 spectral "
               "bands including Red-Edge and NIR (400–1000 nm); global shutter; "
               "&gt;= 1.2 MP per band; downwelling light/irradiance sensor (DLS) and "
               "calibrated reflectance panel for radiometric correction; GPS-tagged "
               "16-bit TIFF output. <b>Minimum viable configuration:</b> DJI Mavic 3M "
               "(all-in-one, blade + site products). <b>Recommended full configuration:</b> "
               "DJI Matrice 350 RTK carrying MicaSense Altum-PT (multispectral + thermal "
               "in one flight)."))

# ---------------- 6. Datasets & formats ----------------
story.append(P("6. Required Datasets &amp; File Formats", "H1x"))
story.append(P("The table below lists every dataset the project consumes or "
               "produces, with its source, file format and extension."))

story.append(P("6.1 Input datasets", "H2x"))
story.append(make_table(
    ["Dataset (Name)", "Source / Sensor", "Format", "Extension(s)"],
    [
        ["UAV multispectral blade/tower captures",
         "MicaSense RedEdge-MX / Altum-PT, DJI Mavic 3M (5–7 bands)",
         "16-bit GeoTIFF per band; raw sensor capture", ".tif / .tiff, .dng"],
        ["Radiometric calibration panel images",
         "Same UAV sensor, pre/post-flight panel shots",
         "16-bit TIFF + panel reflectance sheet", ".tif, .csv"],
        ["Sentinel-2 L2A scenes (site &amp; environment)",
         "ESA Copernicus Open Access / AWS Open Data",
         "SAFE archive with JPEG2000 band files, XML metadata", ".SAFE (folder), .jp2, .xml"],
        ["Landsat 8/9 Collection-2 Level-2 scenes",
         "USGS EarthExplorer",
         "Cloud-Optimized GeoTIFF + MTL metadata", ".tif, .txt / .xml (MTL)"],
        ["Digital elevation model (terrain)",
         "Copernicus DEM GLO-30 / SRTM",
         "GeoTIFF raster", ".tif"],
        ["Turbine asset registry &amp; farm boundary",
         "Operator GIS / survey",
         "Vector layers (points, polygons)", ".gpkg, .shp (+.dbf/.shx/.prj), .geojson"],
        ["UAV flight logs &amp; telemetry",
         "Flight controller export",
         "Tabular log / GPS track", ".csv, .log, .gpx"],
        ["Weather &amp; wind data (QA filtering)",
         "ERA5 reanalysis / met mast",
         "NetCDF grids or tables", ".nc, .csv"],
        ["Public blade-defect training data (e.g. DTU 'Nordtank' turbine inspection images)",
         "DTU Data / Mendeley open repositories",
         "Annotated RGB/NIR images", ".jpg, .png"],
    ],
    [4.6 * cm, 4.0 * cm, 4.4 * cm, 3.5 * cm]))

story.append(P("6.2 Labels, models and intermediate data", "H2x"))
story.append(make_table(
    ["Dataset (Name)", "Produced by", "Format", "Extension(s)"],
    [
        ["Defect annotation labels",
         "Manual labelling (QGIS / CVAT / Label Studio)",
         "COCO JSON, YOLO text labels, mask rasters", ".json, .txt, .png"],
        ["Calibrated reflectance orthomosaics",
         "OpenDroneMap / WebODM (WP2)",
         "Multi-band Cloud-Optimized GeoTIFF", ".tif"],
        ["Index rasters (NDVI / NDRE / EVI)",
         "NumPy / xarray pipeline (WP3)",
         "Single-band GeoTIFF; gridded stacks", ".tif, .nc"],
        ["Trained ML model weights",
         "PyTorch / YOLO training (WP4)",
         "Serialized weights; portable inference model", ".pt / .pth, .onnx"],
        ["Anomaly / defect masks",
         "OpenCV + model inference (WP4)",
         "Binary/label mask rasters", ".png, .tif"],
    ],
    [4.6 * cm, 4.0 * cm, 4.4 * cm, 3.5 * cm]))

story.append(P("6.3 Output / deliverable datasets", "H2x"))
story.append(make_table(
    ["Dataset (Name)", "Consumed by", "Format", "Extension(s)"],
    [
        ["Defect detection layer (geometry + severity class)",
         "QGIS, web dashboard, CMMS",
         "GeoPackage / GeoJSON vector layers; PostGIS tables", ".gpkg, .geojson (+ SQL)"],
        ["Land-cover &amp; change-detection maps",
         "Environmental compliance reporting",
         "GeoTIFF raster + style file", ".tif, .qml / .sld"],
        ["Inspection report per campaign",
         "O&amp;M engineers, asset owners",
         "PDF report; tabular defect register", ".pdf, .csv / .xlsx"],
        ["Web map tiles &amp; dashboard layers",
         "GeoServer / Leaflet / Streamlit",
         "XYZ/WMTS tile cache, MBTiles", ".png (tiles), .mbtiles"],
        ["Pipeline metadata &amp; lineage",
         "Airflow / audit",
         "Run logs, STAC item metadata", ".json, .log"],
    ],
    [4.6 * cm, 4.0 * cm, 4.4 * cm, 3.5 * cm]))
story.append(Spacer(1, 0.2 * cm))
story.append(P("Conventions: all rasters are EPSG-referenced GeoTIFFs (Cloud-Optimized "
               "where served over the web); vectors default to GeoPackage (.gpkg) to avoid "
               "multi-file shapefile handling; naming pattern "
               "<i>&lt;site&gt;_&lt;turbine&gt;_&lt;date&gt;_&lt;product&gt;.&lt;ext&gt;</i>, "
               "e.g. <i>WF01_T07_20260723_ndvi.tif</i>."))

# ---------------- 6. Sample outputs ----------------
story.append(P("7. Sample Outputs (Synthetic Demonstration Images)", "H1x"))
story.append(P("The images below are synthetic samples generated with NumPy + "
               "Matplotlib to illustrate the expected products. Production outputs "
               "will use real UAV and Sentinel-2 data processed through the stack "
               "in Section 4 over the datasets in Section 5."))

story.append(P("7.1 Site analysis product — multispectral bands and NDVI", "H2x"))
img1 = Image(f"{OUT}/site_ndvi_sample.png", width=16.5 * cm, height=4.55 * cm)
story.append(img1)
story.append(Paragraph("Figure 1 — Simulated green/red/NIR reflectance and derived NDVI over a wind farm site. "
                       "Turbine symbols mark asset locations; low-NDVI areas (water body, bare soil) are "
                       "automatically excluded from vegetation-compliance monitoring.", styles["Cap"]))

story.append(P("7.2 Blade inspection product — NIR capture and automated defect mask", "H2x"))
img2 = Image(f"{OUT}/blade_defect_sample.png", width=15.5 * cm, height=8.25 * cm)
story.append(img2)
story.append(Paragraph("Figure 2 — Simulated UAV NIR image of a blade (top) and the automated anomaly "
                       "detection overlay (bottom): leading-edge erosion, a surface crack and a moisture-ingress "
                       "zone are flagged in red with yellow region-of-interest markers.", styles["Cap"]))

# ---------------- 5. Pipeline ----------------
story.append(P("8. Processing Pipeline", "H1x"))
story.append(make_table(
    ["Step", "Stage", "Open-source tools"],
    [
        ["1", "Acquire — UAV flight plans / satellite scene download", "OpenDroneMap ground control, sentinelsat/pystac-client"],
        ["2", "Calibrate — radiometric correction, reflectance panels", "OpenDroneMap, Rasterio, NumPy"],
        ["3", "Register &amp; mosaic — band alignment, orthomosaic", "OpenDroneMap/WebODM, GDAL"],
        ["4", "Analyze — indices (NDVI/NDRE), anomaly masks", "NumPy, xarray, OpenCV, scikit-image"],
        ["5", "Detect — ML defect classification &amp; severity grading", "PyTorch, segmentation-models-pytorch, YOLO"],
        ["6", "Store &amp; serve — geodata layers, tiles, dashboard", "PostGIS, GeoServer, Leaflet, Streamlit"],
        ["7", "Report — automated inspection PDFs, trend charts", "Matplotlib, ReportLab, Airflow (scheduling)"],
    ],
    [1.2 * cm, 7.6 * cm, 7.7 * cm]))

# ---------------- 9. Workflow & methodology ----------------
story.append(P("9. Workflow &amp; Methodology Adopted", "H1x"))
story.append(P("Delivery follows an <b>agile, phased methodology</b>: the analytics "
               "components (WP3–WP4) use a <b>CRISP-DM adapted loop</b> (business "
               "understanding → data understanding → preparation → modelling → "
               "evaluation → deployment), while field operations follow a fixed, "
               "auditable inspection workflow per campaign. Every stage has an "
               "entry criterion, an exit (QA) gate and a named artefact, so a "
               "campaign is traceable end-to-end."))

story.append(P("9.1 End-to-end inspection workflow (per campaign)", "H2x"))
story.append(make_table(
    ["#", "Workflow step", "Method / procedure", "Exit gate → artefact"],
    [
        ["1", "Campaign planning",
         "Select turbines/site; define flight plans (orbit per blade side, lawn-mower grid for site); check weather window and permits.",
         "Approved flight plan → mission file (.kmz/.plan)"],
        ["2", "Pre-flight calibration",
         "Capture reflectance panel; verify DLS; RTK fix confirmed; sensor self-test.",
         "Calibration checklist passed → panel images (.tif)"],
        ["3", "Data acquisition",
         "Automated waypoint flight; 75–85% overlap; GSD per product spec; turbine stopped &amp; locked for blade scans.",
         "Coverage check on-site → raw band captures (.tif)"],
        ["4", "Ingest &amp; preprocessing",
         "Radiometric correction, band alignment, orthomosaic (OpenDroneMap); reflectance conversion.",
         "QA-1 data gate → calibrated orthomosaic (.tif)"],
        ["5", "Analytics &amp; detection",
         "Index computation (NDVI/NDRE); ML inference for defect classes; severity grading rules.",
         "QA-2 model gate → defect layer (.gpkg)"],
        ["6", "Human review (QA)",
         "Analyst reviews flagged defects in QGIS/dashboard; confirms, edits or rejects each detection.",
         "QA-3 review gate → verified defect register (.csv)"],
        ["7", "Reporting &amp; handover",
         "Automated PDF report; dashboard update; export to CMMS; archive with lineage metadata.",
         "AC sign-off → campaign report (.pdf)"],
    ],
    [0.8 * cm, 3.2 * cm, 7.2 * cm, 5.3 * cm]))

story.append(P("9.2 ML model development methodology (CRISP-DM adapted)", "H2x"))
for b in [
    "Data understanding — exploratory band statistics on pilot flights; label taxonomy fixed with O&amp;M engineers (crack, erosion, moisture, lightning, other).",
    "Preparation — tiling, augmentation, band-stacking; 70/15/15 train/validation/test split, stratified by turbine and defect class; test set frozen before training.",
    "Modelling — baseline classical CV first (thresholds/morphology), then U-Net segmentation and YOLO detection; experiments tracked in MLflow (open source).",
    "Evaluation — metrics on the frozen test set only (Section 10 AC thresholds); error review board with a blade engineer before any release.",
    "Deployment — versioned ONNX export; inference in the Airflow pipeline; shadow-mode run for one campaign before replacing the incumbent model.",
    "Monitoring — drift checks on band histograms and detection rates each campaign; retraining triggered when AC metrics degrade.",
]:
    story.append(B(b))

# ---------------- 10. QA & Acceptance criteria ----------------
story.append(P("10. Quality Assurance (QA) &amp; Acceptance Criteria (AC) Report", "H1x"))
story.append(P("QA is enforced at three gates in the workflow (Section 9.1); a "
               "campaign is accepted only when every AC in the table below is met. "
               "Each campaign produces a QA/AC report recording the measured value "
               "against each criterion, signed by the analyst and the client's "
               "O&amp;M representative."))

story.append(P("10.1 QA gates and checks", "H2x"))
story.append(make_table(
    ["Gate", "Scope", "Checks performed"],
    [
        ["QA-1 — Data quality",
         "Raw captures &amp; orthomosaic",
         "Image sharpness (blur metric), exposure/histogram sanity, band-to-band alignment error, forward/side overlap achieved, GSD achieved, radiometric panel deviation, GNSS fix quality, coverage completeness vs flight plan."],
        ["QA-2 — Model output",
         "Indices &amp; ML detections",
         "Index value ranges plausible (NDVI within [-1, 1], no saturation), detection confidence distribution reviewed, per-class counts vs historical norms, no empty/failed tiles, model version and checksum logged."],
        ["QA-3 — Human review",
         "Defect register",
         "100% of Severity 3+ detections reviewed by analyst; &gt;=20% random sample of lower severities; inter-analyst agreement spot-checks; final register free of duplicates and geometry errors."],
    ],
    [3.4 * cm, 3.4 * cm, 9.7 * cm]))

story.append(P("10.2 Acceptance criteria (AC)", "H2x"))
story.append(make_table(
    ["ID", "Acceptance criterion", "Threshold", "Verification method"],
    [
        ["AC-1", "Blade coverage per inspected turbine", "&gt;= 95% of blade surface imaged (all 3 blades, both sides + leading/trailing edge)", "Coverage map vs blade CAD footprint"],
        ["AC-2", "Ground sample distance (blade products)", "&lt;= 3 mm/px on blade surfaces", "EXIF/flight-log distance &amp; sensor model"],
        ["AC-3", "Ground sample distance (site products)", "&lt;= 10 cm/px", "Orthomosaic metadata"],
        ["AC-4", "Georeferencing accuracy", "&lt;= 10 cm RMSE horizontal (RTK), &lt;= 2 px co-registration between epochs", "Check-point residuals report"],
        ["AC-5", "Radiometric calibration", "Panel-derived reflectance within ±5% of certified values per band", "Calibration report per flight"],
        ["AC-6", "Defect detection recall (Severity 3+)", "&gt;= 90% on frozen test set and field-verified sample", "Confusion matrix in QA/AC report"],
        ["AC-7", "Defect detection precision (all classes)", "&gt;= 80% (false positives &lt;= 20%)", "Confusion matrix in QA/AC report"],
        ["AC-8", "Human review completion", "100% Severity 3+, &gt;= 20% sample of lower severities", "Review log export"],
        ["AC-9", "Report turnaround", "Draft report &lt;= 3 working days after last flight; final &lt;= 5 after review", "Timestamps in Airflow lineage"],
        ["AC-10", "Data completeness &amp; lineage", "All deliverables present, named per convention, with STAC metadata and checksums", "Automated manifest validation"],
    ],
    [1.5 * cm, 5.1 * cm, 5.5 * cm, 4.4 * cm]))
story.append(Spacer(1, 0.2 * cm))
story.append(P("<b>QA/AC report contents (per campaign):</b> campaign summary "
               "(site, turbines, dates, crew, weather), flight log table, QA-1/2/3 "
               "gate results with measured values, AC table with pass/fail per "
               "criterion, confusion matrix and metric plots, deviations &amp; "
               "waivers with justification, and sign-off block (analyst, QA lead, "
               "client representative). The report is generated automatically by "
               "the ReportLab pipeline and archived alongside the campaign data."))

# ---------------- 11. Deliverables ----------------
story.append(P("11. Deliverables", "H1x"))
for b in [
    "D1 — Calibrated multispectral orthomosaics per turbine/site (GeoTIFF).",
    "D2 — Defect detection layer with severity classes (GeoPackage/PostGIS).",
    "D3 — NDVI / land-cover / change-detection maps for environmental compliance.",
    "D4 — Web dashboard (Leaflet/Streamlit) with per-turbine inspection history.",
    "D5 — Automated PDF inspection reports with QA/AC section (per flight campaign).",
    "D6 — Reproducible open-source pipeline (containerized, Apache Airflow DAGs).",
]:
    story.append(B(b))

# ---------------- 7. Standards & assumptions ----------------
story.append(P("12. Standards, Assumptions &amp; Constraints", "H1x"))
for b in [
    "Inspection practice aligned with IEC 61400 series and DNV-GL blade inspection guidance.",
    "UAV operations subject to local aviation (e.g. DGCA/FAA/EASA) rules; flights only in permitted wind conditions.",
    "Multispectral sensor with at least 5 bands (B, G, R, RedEdge, NIR); SWIR/thermal optional add-ons.",
    "All software components are OSI-approved open source; AGPL components (WebODM, YOLO) used as services to keep licensing obligations contained.",
    "Sample images in this document are synthetic and for illustration only.",
]:
    story.append(B(b))

doc = SimpleDocTemplate(PDF, pagesize=A4,
                        leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                        title="Multispectral Imagery for Wind Turbine Applications — Scope",
                        author="Project Team")
doc.build(story)
print("PDF written:", PDF)
