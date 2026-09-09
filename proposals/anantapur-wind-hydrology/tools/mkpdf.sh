#!/bin/bash
# Build the proposal as .docx and .pdf.
#
# The contents page carries real page numbers, which are only knowable once the
# document has been laid out. So this runs a two-pass build: render, read back
# where each heading landed, rebuild with those numbers, and repeat until the
# pagination stops moving (normally 2 passes).
#
# Requires: node + the `docx` npm package, libreoffice-writer, poppler-utils.
set -euo pipefail
cd "$(dirname "$0")"
OUT="${1:-proposal}"
export HOME="$PWD"

for pass in 1 2 3 4; do
  [ -f toc.json ] && export TOC_JSON=toc.json || unset TOC_JSON
  node build_proposal.js "$OUT.docx" >/dev/null
  rm -f "$OUT.pdf"
  soffice -env:UserInstallation=file:///tmp/loprof_build --headless --norestore \
          --convert-to pdf "$OUT.docx" --outdir . >/dev/null 2>&1

  if python3 - "$OUT" <<'PY'
import json, os, re, subprocess, sys
out = sys.argv[1]
pages = subprocess.run(['pdftotext', '-layout', f'{out}.pdf', '-'],
                       capture_output=True, text=True).stdout.split('\f')
found = {}
for i, pg in enumerate(pages, 1):
    for line in pg.splitlines():
        l = ' '.join(line.split())
        if re.search(r'\.{3,}\s*\d*$', l):      # skip the contents page's own lines
            continue
        if re.match(r'^(\d+\.\s[A-Z].*|\d+\.\d+\s[A-Z].*)$', l):
            found.setdefault(l, i)
prev = json.load(open('toc.json')) if os.path.exists('toc.json') else None
json.dump(found, open('toc.json', 'w'), indent=1)
print(f"  pass: {len(found)} headings, {len(pages)-1} pages"
      f"{' - stable' if prev == found else ''}")
sys.exit(0 if prev == found else 1)
PY
  then
    echo "Built $OUT.docx and $OUT.pdf"
    exit 0
  fi
done
echo "Warning: pagination did not settle after 4 passes; check the contents page." >&2
