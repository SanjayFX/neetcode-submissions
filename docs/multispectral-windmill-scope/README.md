# Multispectral Imagery for Wind Turbine Applications — Scope

- `Multispectral_Windmill_Scope.pdf` — project scope document (open-source stack, pipeline, deliverables, sample outputs).
- `gen_images.py` — generates the synthetic sample images (`site_ndvi_sample.png`, `blade_defect_sample.png`) with NumPy + Matplotlib.
- `build_pdf.py` — builds the PDF with ReportLab, embedding the sample images.

Rebuild:

```bash
pip install numpy matplotlib reportlab
python3 gen_images.py && python3 build_pdf.py
```

Note: the sample images are synthetic, for illustration only.
