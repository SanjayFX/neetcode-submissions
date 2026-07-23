"""Generate synthetic multispectral sample outputs for the scope PDF."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

rng = np.random.default_rng(42)
OUT = "."

# ---------------------------------------------------------------
# Figure 1: Simulated multispectral bands + NDVI for site analysis
# ---------------------------------------------------------------
H, W = 200, 200
yy, xx = np.mgrid[0:H, 0:W]

# Base landscape: vegetation gradient + water body + bare soil patch
veg = 0.5 + 0.4 * np.sin(xx / 40.0) * np.cos(yy / 55.0)
veg += 0.15 * rng.standard_normal((H, W))
veg = np.clip(veg, 0, 1)

water = ((xx - 160) ** 2 + (yy - 40) ** 2) < 900          # lake
soil = ((xx - 40) ** 2 / 2 + (yy - 150) ** 2) < 1600      # bare patch

# Synthetic reflectance per band
red = 0.25 - 0.15 * veg
nir = 0.20 + 0.55 * veg
green = 0.18 + 0.10 * veg
rededge = 0.20 + 0.35 * veg

for band in (red, nir, green, rededge):
    band[water] = 0.04
    band[soil] = 0.30
nir[soil] = 0.34

ndvi = (nir - red) / (nir + red + 1e-9)

# Turbine locations
turbines = [(50, 60), (100, 90), (150, 120), (75, 160), (170, 55)]

fig, axes = plt.subplots(1, 4, figsize=(16, 4.4))
cmaps = ["Greens", "Reds", "PuRd", "RdYlGn"]
data = [green, red, nir, ndvi]
titles = ["Green band (560 nm)", "Red band (668 nm)",
          "NIR band (840 nm)", "NDVI (site vegetation map)"]
for ax, d, t, cm in zip(axes, data, titles, cmaps):
    im = ax.imshow(d, cmap=cm)
    ax.set_title(t, fontsize=11)
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
for ax in axes:
    for tx, ty in turbines:
        ax.plot(tx, ty, marker="2", color="black", markersize=14, mew=2)
axes[3].plot([], [], marker="2", color="black", linestyle="none",
             markersize=10, mew=2, label="Turbine")
axes[3].legend(loc="lower right", fontsize=8)
fig.suptitle("Simulated Multispectral Bands & NDVI — Wind Farm Site Analysis (synthetic sample)",
             fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f"{OUT}/site_ndvi_sample.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------
# Figure 2: Blade inspection — NIR image with defect detection
# ---------------------------------------------------------------
BH, BW = 160, 480
byy, bxx = np.mgrid[0:BH, 0:BW]

# Blade shape: tapered ellipse-ish mask
cy = BH / 2
half = 55 * (1 - bxx / (BW * 1.15)) + 8
blade = np.abs(byy - cy) < half

nir_blade = np.full((BH, BW), 0.08)
nir_blade[blade] = 0.75 + 0.02 * rng.standard_normal(blade.sum())

# Defects: leading-edge erosion (streak), crack (line), moisture ingress (blob)
defects = []
# erosion streak along leading edge
er = (np.abs(byy - (cy - half + 4)) < 3) & (bxx > 300) & (bxx < 420) & blade
nir_blade[er] -= 0.25
defects.append(("Leading-edge erosion", 360, int(cy - 30), 40))
# crack
cr = (np.abs((byy - cy) - 0.35 * (bxx - 150)) < 1.5) & (bxx > 150) & (bxx < 185) & blade
nir_blade[cr] -= 0.35
defects.append(("Surface crack", 168, int(cy + 6), 26))
# moisture blob
mo = ((bxx - 80) ** 2 + (byy - cy - 10) ** 2) < 130
mo &= blade
nir_blade[mo] -= 0.18
defects.append(("Moisture ingress", 80, int(cy + 10), 20))

fig, axes = plt.subplots(2, 1, figsize=(12, 6.4))
axes[0].imshow(nir_blade, cmap="gray", vmin=0, vmax=1)
axes[0].set_title("UAV NIR capture — turbine blade, suction side (synthetic sample)", fontsize=11)
axes[0].set_xticks([]); axes[0].set_yticks([])

# Detection overlay: simple anomaly threshold inside the blade
anom = blade & (nir_blade < 0.55)
overlay = np.stack([nir_blade] * 3, axis=-1)
overlay[anom] = [1.0, 0.15, 0.1]
axes[1].imshow(overlay)
for name, dx, dy, r in defects:
    circ = Circle((dx, dy), r, fill=False, color="yellow", lw=1.8)
    axes[1].add_patch(circ)
    ly = dy + r + 14 if dy - r - 6 < 8 else dy - r - 6
    axes[1].annotate(name, (dx, ly), color="yellow",
                     fontsize=9, ha="center", weight="bold")
axes[1].set_title("Automated defect detection output (OpenCV/scikit-image anomaly mask)", fontsize=11)
axes[1].set_xticks([]); axes[1].set_yticks([])
fig.tight_layout()
fig.savefig(f"{OUT}/blade_defect_sample.png", dpi=150)
plt.close(fig)

print("images written")
