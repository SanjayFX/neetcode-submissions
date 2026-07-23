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

story.append(PageBreak())

# ---------------- 4. Sample outputs ----------------
story.append(P("5. Sample Outputs (Synthetic Demonstration Images)", "H1x"))
story.append(P("The images below are synthetic samples generated with NumPy + "
               "Matplotlib to illustrate the expected products. Production outputs "
               "will use real UAV and Sentinel-2 data processed through the stack "
               "in Section 4."))

story.append(P("5.1 Site analysis product — multispectral bands and NDVI", "H2x"))
img1 = Image(f"{OUT}/site_ndvi_sample.png", width=16.5 * cm, height=4.55 * cm)
story.append(img1)
story.append(Paragraph("Figure 1 — Simulated green/red/NIR reflectance and derived NDVI over a wind farm site. "
                       "Turbine symbols mark asset locations; low-NDVI areas (water body, bare soil) are "
                       "automatically excluded from vegetation-compliance monitoring.", styles["Cap"]))

story.append(P("5.2 Blade inspection product — NIR capture and automated defect mask", "H2x"))
img2 = Image(f"{OUT}/blade_defect_sample.png", width=15.5 * cm, height=8.25 * cm)
story.append(img2)
story.append(Paragraph("Figure 2 — Simulated UAV NIR image of a blade (top) and the automated anomaly "
                       "detection overlay (bottom): leading-edge erosion, a surface crack and a moisture-ingress "
                       "zone are flagged in red with yellow region-of-interest markers.", styles["Cap"]))

# ---------------- 5. Pipeline ----------------
story.append(P("6. Processing Pipeline", "H1x"))
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

# ---------------- 6. Deliverables ----------------
story.append(P("7. Deliverables", "H1x"))
for b in [
    "D1 — Calibrated multispectral orthomosaics per turbine/site (GeoTIFF).",
    "D2 — Defect detection layer with severity classes (GeoPackage/PostGIS).",
    "D3 — NDVI / land-cover / change-detection maps for environmental compliance.",
    "D4 — Web dashboard (Leaflet/Streamlit) with per-turbine inspection history.",
    "D5 — Automated PDF inspection reports (per flight campaign).",
    "D6 — Reproducible open-source pipeline (containerized, Apache Airflow DAGs).",
]:
    story.append(B(b))

# ---------------- 7. Standards & assumptions ----------------
story.append(P("8. Standards, Assumptions &amp; Constraints", "H1x"))
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
