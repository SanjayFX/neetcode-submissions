const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageBreak,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, LevelFormat,
  Header, Footer, PageNumber, convertInchesToTwip, TableOfContents,
  Tab, TabStopType, LeaderType,
} = require('docx');

/* ---------- constants ---------- */
const NAVY = '1F3864';
const ACCENT = '2E74B5';
const GREY = '595959';
const HDRFILL = '1F3864';
const ALTFILL = 'EEF3F9';
const NOTEFILL = 'FFF4E5';

const PAGE_W = 11906, MARGIN = 1080;
const TW = PAGE_W - 2 * MARGIN; // 9746 usable

/* ---------- helpers ---------- */
const P = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after === undefined ? 120 : o.after, before: o.before || 0, line: 264 },
  indent: o.indent,
  border: o.border,
  shading: o.shading,
  children: [new TextRun({ text, bold: o.bold, italics: o.italics, size: o.size || 20, color: o.color, font: 'Calibri' })],
});

// rich paragraph: array of [text, {bold,italics,color}]
const RP = (parts, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after === undefined ? 120 : o.after, before: o.before || 0, line: 264 },
  indent: o.indent, border: o.border, shading: o.shading,
  children: parts.map(([t, f = {}]) => new TextRun({
    text: t, bold: f.bold, italics: f.italics, color: f.color, size: f.size || o.size || 20, font: 'Calibri',
  })),
});

const tocEntries = [];
let PAGEMAP = {};
const tocNorm = (t) => String(t).replace(/\s+/g, ' ').trim();
try {
  if (process.env.TOC_JSON) {
    const raw = JSON.parse(fs.readFileSync(process.env.TOC_JSON, 'utf8'));
    // PDF text extraction collapses runs of whitespace, so match on a normalised key
    for (const k of Object.keys(raw)) PAGEMAP[tocNorm(k)] = raw[k];
  }
} catch (e) { PAGEMAP = {}; }

const H1 = (text) => (tocEntries.push({ text, lvl: 1 }), new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 320, after: 180 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: ACCENT, space: 6 } },
  children: [new TextRun({ text, bold: true, size: 28, color: NAVY, font: 'Calibri' })],
}));

const H2 = (text) => (tocEntries.push({ text, lvl: 2 }), new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 260, after: 120 },
  children: [new TextRun({ text, bold: true, size: 23, color: ACCENT, font: 'Calibri' })],
}));

const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 200, after: 100 },
  children: [new TextRun({ text, bold: true, size: 21, color: '333333', font: 'Calibri' })],
});

const BUL = (text, lvl = 0) => new Paragraph({
  numbering: { reference: 'bullets', level: lvl },
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 70, line: 264 },
  children: [new TextRun({ text, size: 20, font: 'Calibri' })],
});

// bullet with a bold lead-in "Label — rest"
const BULL = (label, rest, lvl = 0) => new Paragraph({
  numbering: { reference: 'bullets', level: lvl },
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 70, line: 264 },
  children: [
    new TextRun({ text: label, bold: true, size: 20, font: 'Calibri' }),
    new TextRun({ text: rest, size: 20, font: 'Calibri' }),
  ],
});

const SPACER = (h = 120) => new Paragraph({ spacing: { after: h }, children: [] });

function cell(text, o = {}) {
  const runs = (Array.isArray(text) && text.every(Array.isArray)) ? text : [[text, {}]];
  return new TableCell({
    width: { size: o.w, type: WidthType.DXA },
    shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    verticalAlign: o.va || 'top',
    columnSpan: o.span,
    children: [new Paragraph({
      alignment: o.align || AlignmentType.LEFT,
      spacing: { after: 0, line: 250 },
      children: runs.map(([t, f = {}]) => new TextRun({
        text: t, bold: o.bold || f.bold, italics: f.italics,
        color: o.color || f.color, size: o.size || 18, font: 'Calibri',
      })),
    })],
  });
}

function makeTable(widths, header, rows, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const trs = [];
  if (header) {
    trs.push(new TableRow({
      tableHeader: true,
      children: header.map((h, i) => cell(h, { w: widths[i], fill: HDRFILL, bold: true, color: 'FFFFFF', align: i && opts.centerHdr ? AlignmentType.CENTER : AlignmentType.LEFT })),
    }));
  }
  rows.forEach((r, ri) => {
    if (r.__section) {
      trs.push(new TableRow({ children: [cell(r.__section, { w: total, span: widths.length, fill: 'D9E2F3', bold: true, color: NAVY })] }));
      return;
    }
    const fill = r.__fill || (ri % 2 ? ALTFILL : undefined);
    const cells = (r.cells || r).map((c, i) => cell(c, {
      w: widths[i], fill,
      bold: r.__bold,
      align: opts.rightCols && opts.rightCols.includes(i) ? AlignmentType.RIGHT : (opts.centerCols && opts.centerCols.includes(i) ? AlignmentType.CENTER : AlignmentType.LEFT),
    }));
    trs.push(new TableRow({ children: cells }));
  });
  return new Table({
    columnWidths: widths,
    width: { size: total, type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: 'A6A6A6' },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: 'A6A6A6' },
      left: { style: BorderStyle.SINGLE, size: 4, color: 'A6A6A6' },
      right: { style: BorderStyle.SINGLE, size: 4, color: 'A6A6A6' },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
    },
    rows: trs,
  });
}

// callout box
const NOTE = (title, lines, fill = NOTEFILL) => new Table({
  columnWidths: [TW],
  width: { size: TW, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 4, color: 'E0A45E' },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: 'E0A45E' },
    left: { style: BorderStyle.SINGLE, size: 18, color: 'E0A45E' },
    right: { style: BorderStyle.SINGLE, size: 4, color: 'E0A45E' },
    insideHorizontal: { style: BorderStyle.NONE },
    insideVertical: { style: BorderStyle.NONE },
  },
  rows: [new TableRow({
    children: [new TableCell({
      width: { size: TW, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill, color: 'auto' },
      margins: { top: 130, bottom: 130, left: 180, right: 160 },
      children: [
        new Paragraph({ spacing: { after: 70 }, children: [new TextRun({ text: title, bold: true, size: 20, color: '8A4B08', font: 'Calibri' })] }),
        ...lines.map((l, i) => new Paragraph({
          alignment: AlignmentType.JUSTIFIED,
          spacing: { after: i === lines.length - 1 ? 0 : 70, line: 264 },
          children: [new TextRun({ text: l, size: 19, font: 'Calibri' })],
        })),
      ],
    })],
  })],
});

const R = (n) => '₹ ' + n;

/* ================= DOCUMENT CONTENT ================= */
const children = [];

/* ---- COVER ---- */
children.push(
  new Paragraph({ spacing: { after: 900 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: 'TECHNO-COMMERCIAL PROPOSAL', bold: true, size: 40, color: NAVY, font: 'Calibri' })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 360 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 10 } },
    children: [new TextRun({ text: 'Comprehensive Hydrology, Hydraulics and Drainage Design Study', size: 26, color: GREY, font: 'Calibri' })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new TextRun({ text: 'Proposed Wind Power Project', bold: true, size: 28, color: '333333', font: 'Calibri' })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 700 },
    children: [new TextRun({ text: 'Anantapur District, Andhra Pradesh', size: 24, color: GREY, font: 'Calibri' })],
  }),
);

children.push(makeTable([2600, 7146], null, [
  [[['Document title', { bold: true }]], 'Techno-Commercial Proposal — Hydrology, Hydraulics & Drainage Design Study'],
  [[['Prepared for', { bold: true }]], ' '],
  [[['Prepared by', { bold: true }]], ' '],
  [[['Proposal reference', { bold: true }]], ' '],
  [[['Revision', { bold: true }]], 'R0 — for Client review'],
  [[['Date of issue', { bold: true }]], ' '],
  [[['Validity', { bold: true }]], '60 (sixty) days from date of issue'],
  [[['In response to', { bold: true }]], "Client's e-mail on scope of work, methodology and report submission for Hydrology Studies"],
]));

children.push(new Paragraph({ spacing: { before: 500 }, children: [] }));
children.push(NOTE('Read this first — two items are still awaited', [
  'This proposal has been prepared from the written scope conveyed by the Client. Two referenced attachments were not received with that correspondence and are not reflected here: (i) the Scope of Work / Methodology / Reports document, and (ii) the georeferenced project (pink) boundary.',
  'Every quantity in Section 10 (Commercials) is driven by the enclosed boundary area, which has been assumed at 80 sq km pending receipt of the KML/shapefile. Unit rates are firm; the totals will be restated against the actual notified area on receipt, at no change to the rates.',
  'Where site-specific hydrological figures are quoted in Section 3, they are indicative regional values stated to establish the basis of design. All are to be replaced with values derived from primary IMD and CWC records during Stage 1 and confirmed in the Inception Report.',
]));

children.push(new Paragraph({ children: [new PageBreak()] }));

/* ---- TOC ---- */
children.push(H1('Contents'));
const TOC_AT = children.length;      // static contents spliced in here after all headings are known
children.push(new Paragraph({ children: [new PageBreak()] }));

/* ---- 1. UNDERSTANDING ---- */
children.push(H1('1.  Understanding of the Requirement'));
children.push(P('We have reviewed the Client’s instructions and set out below our understanding of what is required. The whole of the proposal that follows is built on these five points; if any is misread, please tell us and we will reissue.'));

children.push(makeTable([600, 3400, 5746], ['#', 'Client instruction', 'How this proposal responds'], [
  ['1', [['Assess the entire wind project boundary.', { bold: true }], [' The 35 proposed WTG coordinates are tentative and are to be disregarded.', {}]],
    'The whole notified boundary is modelled as a single continuous domain. No part of the study is anchored to a turbine coordinate. The principal design output is a boundary-wide hydrological constraint surface (Section 6.8.1) against which any future layout can be tested, so that the study does not expire when the layout changes.'],
  ['2', [['Design for a 50–75 year horizon.', { bold: true }]],
    'Return periods are raised above the statutory minima (Section 4.2) and a climate-change uplift derived from CMIP6 projections for the 2050s and 2075s horizons is applied to design rainfall (Section 6.5). A residual-risk register for the full asset life is issued at Stage 9.'],
  ['3', [['Black cotton soil governs everything.', { bold: true }], [' Small rainfall renders the site inaccessible until it dries.', {}]],
    'Vertisol behaviour is treated as a primary design driver, not a footnote. We map swell potential and soaked CBR across the boundary, model ponding duration (not merely peak depth), and issue a month-by-month trafficability calendar (Section 6.8.9) alongside subgrade and drainage treatments specific to expansive soils (Section 6.8.3).'],
  ['4', [['All WTGs are interconnected by road; village bypasses lead into and out of the farm.', { bold: true }]],
    'The internal road network and its external connections are treated as one drainage system. Alignment, vertical-profile, cross-drainage and side-drain recommendations are issued for the network as a whole, including the interaction of the bypasses with village drainage and irrigation tanks (Sections 6.8.2, 6.8.4, 6.8.5).'],
  ['5', [['The report must carry implementable advice on road design, drains and related works.', { bold: true }]],
    'Deliverables include a Drainage Master Plan with a sized structure schedule for every crossing, typical design drawings, indicative BOQ and an O&M manual — not a findings-only report. See Section 8.'],
], { centerCols: [0] }));

children.push(P('We note the Client’s stated objective in plain terms: no drainage-related failure, washout or loss of access over the life of the project. That is an availability and safety objective as much as a civil one, and it is the standard against which we have written the scope below.', { before: 200 }));

/* ---- 2. WHY THIS SITE NEEDS A FULL STUDY ---- */
children.push(H1('2.  Site Setting and Why It Governs the Study'));
children.push(P('Anantapur presents an unusual and frequently underestimated combination: one of the lowest mean annual rainfalls in India, delivered in a small number of high-intensity events, onto a soil that becomes effectively impermeable and untrafficable the moment it wets. Low annual rainfall is routinely mistaken for low drainage risk. It is the opposite condition that applies here — the drainage risk is concentrated, flashy and soil-driven.'));

children.push(H2('2.1  Climate and rainfall regime'));
children.push(BULL('Rain-shadow, semi-arid regime. ', 'The district lies in the lee of the Western Ghats and is among the driest in the country, with mean annual rainfall of the order of 520–560 mm. Inter-annual variability is high and drought years are frequent.'));
children.push(BULL('Bimodal delivery. ', 'The South-West monsoon (June–September) supplies the larger share, but the North-East monsoon (October–December) contributes a substantial fraction and, being driven by Bay of Bengal depressions and cyclonic systems, produces the short-duration extremes that govern culvert and drain sizing. A design study that considers only the SW monsoon will undersize the network.'));
children.push(BULL('Extremes are decoupled from the mean. ', 'A single 24-hour event can deliver a third of the annual total. Design must therefore be driven by frequency analysis of the annual maximum series and by site-specific intensity–duration–frequency relationships, never by mean or seasonal totals.'));

children.push(H2('2.2  Terrain, drainage and the tank cascade'));
children.push(BULL('Undulating granitic peneplain ', 'with isolated hillocks and inselbergs; short, steep first-order channels feeding wide, sandy, braided ephemeral streams (vankas) that are dry for most of the year and carry high, sediment-laden flows for hours at a time.'));
children.push(BULL('Penna (Pennar) basin drainage ', 'across most of the district — Chitravathi, Papagni, Pandameru and associated tributaries — with the north-western margin draining towards the Vedavathi/Hagari system. The applicable CWC Flood Estimation Report sub-zone (Krishna & Pennar) will be confirmed at inception.'));
children.push(BULL('Dense minor-irrigation tank cascades. ', 'This is the single largest source of avoidable dispute and redesign on Rayalaseema wind projects. Tanks are linked in series by feeder and surplus channels; a road embankment placed across a surplus course, or a platform inside a tank’s Full Tank Level, creates both a flooding failure and a legal exposure. Tank FTL/MWL/TBL levels and cascade connectivity are mapped explicitly under this scope (Section 6.4).'));
children.push(BULL('Ungauged catchments. ', 'The internal streams carry no discharge gauges. Peak flows must therefore be derived by rainfall-runoff modelling and cross-checked against regional flood formulae and documented historical evidence — which is why the community and physical-evidence survey in Stage 1 is a genuine data source here, not a formality.'));

children.push(H2('2.3  Black cotton soil — the governing constraint'));
children.push(P('The Client’s observation is correct and is the reason this study is scoped the way it is. Vertisols on this site are expected to exhibit:'));
children.push(BUL('High shrink–swell potential — seasonal heave and shrinkage cracking, with deep desiccation cracks that admit water rapidly at the onset of rain and then seal as the clay swells.'));
children.push(BUL('Very low permeability once wetted — infiltration collapses, so almost all rainfall after the first hour becomes runoff. Effective curve numbers approach those of the most impermeable hydrological soil group.'));
children.push(BUL('Severe loss of strength on saturation — soaked CBR values commonly fall to 2–3%, against 8–10% or more when dry. Bearing capacity and trafficability both collapse.'));
children.push(BUL('Long drying times — the same low permeability that generates the runoff prevents the profile from draining, so access is lost for far longer than the rainfall event itself. This is the mechanism behind the Client’s stated experience.'));
children.push(BUL('Aggressive scour of unlined channels — earthen side drains cut in vertisol slough, undercut and collapse. Unlined drainage is not a viable option on this site and has not been assumed anywhere in this proposal.'));

children.push(NOTE('The design consequence', [
  'Because strength loss and loss of access are governed by how long water stands rather than by how deep it gets, this study models ponding duration as a primary output, not merely peak flood depth. Conventional hydrology reports issue depth maps alone; on vertisol they answer the wrong question.',
]));

/* ---- 3. BASIS OF DESIGN ---- */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1('3.  Basis of Design'));
children.push(P('The following basis is proposed for the Client’s approval. It will be fixed in the Inception Report (D1) and will not thereafter change without written instruction, so that every downstream deliverable is traceable to an agreed standard.'));

children.push(H2('3.1  Design life and design horizon'));
children.push(P('The Client has asked for a 50–75 year estimate. We propose to adopt a 75-year design horizon as the governing case, with results also reported at 50 years so that the Client can see the sensitivity and make value-engineering decisions with the numbers in front of them. Structures are separately assessed for serviceable life, since a culvert barrel and its protection works do not age at the same rate.'));

children.push(H2('3.2  Return periods proposed'));
children.push(P('Indian codal practice sets minimum return periods for road drainage; those minima are calibrated to public roads with alternative routes and a shorter design life. For a private, single-access asset network on expansive soil with a 75-year horizon, we recommend adopting the following, which sit above the minima:'));

children.push(makeTable([3050, 1500, 1500, 3696], ['Element', 'Codal minimum (typical)', 'Proposed for this project', 'Rationale'], [
  ['Road side drains / longitudinal drainage', '5–10 yr', '25 yr', 'Failure means loss of access and subgrade saturation, not merely surface flooding. On vertisol the consequence is disproportionate to the cost of upsizing.'],
  ['Pipe and box culverts (minor crossings)', '25 yr', '50 yr', 'Marginal cost of one size increment is small against the cost of a washout and an outage.'],
  ['Major cross-drainage / vented and submersible causeways', '50 yr', '100 yr', 'These are the single-point failures on the network; loss of one severs access to a group of WTGs.'],
  ['WTG platform and hardstand formation level', 'not codified', '100 yr + freeboard', 'Crane pads must remain serviceable for major-component exchange throughout the asset life.'],
  ['Substation / pooling station / O&M building', 'not codified', '200 yr + freeboard', 'Single points of failure for the entire generating asset; the cost of raising the platform is trivial by comparison.'],
  ['Check on all of the above', '—', 'Design event + climate uplift', 'Reported as a separate sensitivity case so residual risk is visible and priced (Section 6.5).'],
], { centerCols: [1, 2] }));

children.push(H2('3.3  Freeboard and check conditions'));
children.push(BUL('Minimum formation level for internal roads: design flood or ponding level for the adopted return period, plus freeboard, with a separate minimum embankment height to hold the subgrade above the zone of capillary rise and seasonal moisture change in the vertisol. Both criteria apply; the governing one is adopted.'));
children.push(BUL('Culvert soffit set clear of the design headwater, with afflux limited to an agreed value and outlet velocity limited to the permissible value for the protection provided.'));
children.push(BUL('Blockage check: all cross-drainage structures re-run at 50% blockage, a routine failure mode where flows carry vertisol sediment, agricultural residue and thorn scrub.'));
children.push(BUL('Antecedent moisture check: design runs at AMC-III, representing a storm arriving on an already-wet profile — the realistic monsoon condition and one that is frequently omitted.'));

children.push(H2('3.4  Codes, standards and references'));
children.push(makeTable([2600, 7146], ['Domain', 'Standards proposed'], [
  ['Road geometry & drainage', 'IRC:SP:20 (Rural Roads Manual); IRC:SP:72 (low-volume rural roads); IRC:SP:42 and IRC:SP:50 (road drainage); IRC:34 (roads in waterlogged areas); IRC:SP:48 where hill-road sections are encountered'],
  ['Cross-drainage structures', 'IRC:SP:13 (small bridges and culverts); IRC:5 (general features of design); IRC:78 (foundations and substructures); IRC:89 (river training and protection works)'],
  ['Pavement & expansive subgrade', 'IRC:37 (flexible pavements); IRC:SP:89 (stabilised road bases, lime/lime–flyash); IS 9451 (guidelines for laying of roads on expansive soils); IS 2720 series (soil testing)'],
  ['Hydrology & hydraulics', 'IS 4410 (glossary); IS 5477 (reservoir capacity); IS 6512 / IS 11223 (spillway and design flood); CWC Flood Estimation Report for the applicable sub-zone; CWC/IMD guidelines on design storm estimation'],
  ['Data sources', 'IMD daily gridded rainfall and station records; IMD short-duration rainfall ratios; India-WRIS; Survey of India toposheets; NRSC Bhuvan; AP Water Resources Department minor-irrigation tank register'],
  ['Climate projections', 'IPCC AR6 / CMIP6 downscaled projections under SSP2-4.5 and SSP5-8.5; CORDEX South Asia where resolution requires'],
]));

/* ---- 4. INPUTS ---- */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1('4.  Inputs Considered and Inputs Required'));
children.push(P('The Client has specifically asked that the inputs considered be set out in the proposal. They fall into three groups.'));

children.push(H2('4.1  Inputs to be provided by the Client'));
children.push(P('These are on the critical path. Items marked essential are required before mobilisation; the programme in Section 9 starts from the date the last of them is received.'));
children.push(makeTable([600, 4300, 1250, 3596], ['#', 'Input', 'Priority', 'Why it is needed'], [
  ['1', 'Georeferenced project boundary (KML / KMZ / SHP) with coordinate system stated', 'Essential', 'Defines the study domain and every quantity in Section 10. Returned to the Client within one week as a verified, styled Google Earth KML with a full area statement (D1a). Not yet received.'],
  ['2', 'Scope of Work / Methodology / Reports document referred to in the Client’s correspondence', 'Essential', 'To reconcile this proposal against the Client’s own document before contract. Not yet received.'],
  ['3', 'Land / revenue records, cadastral or village maps for the boundary; status of land acquisition or lease', 'Essential', 'Survey access, and identification of tank poramboke and water-body land within the boundary.'],
  ['4', 'Concept internal road network and external connection points, including the proposed village bypasses', 'Essential', 'The road network is the subject of the drainage design. If not yet fixed, we will develop an indicative network for assessment (allowed for in Part H).'],
  ['5', 'Proposed substation / pooling station location and evacuation corridor', 'High', 'Highest-consequence assets; drive the 200-year platform check.'],
  ['6', 'WTG model, hardstand and crane-pad dimensions, platform tolerance and permissible gradients', 'High', 'Governs platform sizing, perimeter drainage and formation-level recommendations.'],
  ['7', 'Any existing topographic survey, DEM, LiDAR or drone data for the site', 'Medium', 'May reduce Part B scope and cost. Please share whatever exists, in any state.'],
  ['8', 'Any existing geotechnical investigation, trial pit or borehole data', 'Medium', 'May reduce Part D scope and cost.'],
  ['9', 'Existing EIA, wind resource assessment or feasibility reports for the site', 'Medium', 'Avoids duplication and provides land-use and environmental context.'],
  ['10', 'Site access, security clearance and a nominated Client coordinator for local liaison', 'Essential', 'Required for survey and investigation mobilisation.'],
  ['11', 'Support for landowner permissions for survey and trial pits, and for local administration liaison', 'Essential', 'Access to private agricultural land within the boundary.'],
  ['12', 'Confirmation of intended construction start window and target commissioning date', 'High', 'Drives the trafficability calendar and construction-sequencing advice.'],
], { centerCols: [0, 2] }));

children.push(H2('4.2  Inputs procured and generated by the Consultant'));
children.push(BULL('Secondary hydro-meteorological data — ', 'IMD gridded and station rainfall records (long-period series), short-duration rainfall ratios, evaporation and temperature records, CWC and India-WRIS basin data.'));
children.push(BULL('Cartographic and remote-sensing data — ', 'Survey of India toposheets at 1:50,000, regional DEM for external catchments, and multi-date satellite imagery spanning at least two decades to establish historical inundation extents, gully development, tank behaviour and land-use change.'));
children.push(BULL('Institutional records — ', 'AP Water Resources Department minor-irrigation tank register (FTL, MWL, TBL, ayacut, feeder and surplus channel alignments), district drought and flood records, and any notified water-body schedules.'));
children.push(BULL('Primary survey data — ', 'UAV survey and terrain model, ground control, cross-sections at crossings, and the inventory of existing hydraulic structures (Stage 2).'));
children.push(BULL('Primary geotechnical data — ', 'soil classification, swell, CBR, infiltration and groundwater data across the boundary (Stage 3).'));
children.push(BULL('Historical evidence from the community — ', 'structured interviews with farmers, village elders and local officials on observed flood paths, tank overflow behaviour, road washouts and the duration of access loss. On ungauged ephemeral catchments this is a genuine calibration input, and we treat it as one.'));

children.push(H2('4.3  Assumptions where an input is not available'));
children.push(P('Where a required input is unavailable, we will not stop work. We will adopt a conservative assumption, state it explicitly in the deliverable, quantify the sensitivity of the result to it, and list it in the residual-risk register. No assumption will be buried in an appendix.'));

/* ---- 5. METHODOLOGY OVERVIEW ---- */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1('5.  Methodology — Overview'));
children.push(P('The study runs in nine stages. Stages 2 and 3 are field stages and are weather-dependent; the remainder are desk stages. The logic is deliberately linear: terrain and soil are measured before anything is modelled, the catchment is understood before flows are estimated, flows are established before hydraulics are run, and design advice is issued only once the hydraulics are settled.'));

children.push(makeTable([700, 2700, 6346], ['Stage', 'Title', 'Purpose'], [
  ['1', 'Inception, data acquisition and desk review', 'Assemble all secondary data, reconnoitre the site, capture historical flood evidence, and fix the basis of design.'],
  ['2', 'Topographic survey and terrain model', 'Produce the high-resolution DTM on which every subsequent analysis depends, plus structure inventory and crossing sections.'],
  ['3', 'Soil and sub-surface characterisation', 'Establish vertisol extent, depth, swell potential, soaked CBR, infiltration and groundwater across the boundary.'],
  ['4', 'Catchment delineation and drainage characterisation', 'Define internal and external catchments, stream network, and the irrigation tank cascade and its FTL/MWL constraints.'],
  ['5', 'Hydrological analysis', 'Frequency analysis, site-specific IDF curves, climate-change uplift, and design peak flows and hydrographs at every node.'],
  ['6', '2D hydraulic modelling', 'Rain-on-grid flood modelling of the entire boundary: depth, velocity, hazard, ponding duration, overtopping.'],
  ['7', 'Erosion, scour and sediment assessment', 'Soil loss, sediment yield, gully risk, and scour depths at every crossing.'],
  ['8', 'Design recommendations and Drainage Master Plan', 'The implementable output: constraint mapping, road and drainage design advice, structure schedule, drawings and BOQ.'],
  ['9', 'Lifetime resilience, O&M and handover', 'Residual-risk register, maintenance and monitoring regime, final reporting and workshops.'],
], { centerCols: [0] }));

children.push(NOTE('On the sequencing of the field work', [
  'Stages 2 and 3 must be executed in a dry window. Attempting UAV survey and trial pitting on wetted vertisol produces poor ground control, unusable access and unrepresentative soil samples — precisely the condition the Client has described. The programme in Section 9 assumes mobilisation into a dry window; if the award date falls late in the year, we will advise on resequencing rather than force the field work.',
]));

/* ---- 6. DETAILED SCOPE ---- */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1('6.  Detailed Scope of Work'));

children.push(H2('6.1  Stage 1 — Inception, Data Acquisition and Desk Review'));
children.push(BUL('Georeferencing of the project boundary, establishment of the project coordinate and datum system, and preparation of the GIS base map covering the boundary and its full external contributing catchment.'));
children.push(BULL('Boundary verification and area statement. ', 'On receipt of the Client’s boundary file we will validate its geometry (closure, self-intersection, duplicate and spurious vertices, coordinate system and datum), compute the enclosed area on the WGS84 ellipsoid by an equal-area projection, and reissue the boundary as a clean, styled Google Earth KML carrying the area details. The area statement will report gross area, any excluded internal parcels, and net area in sq km, hectares and acres, together with perimeter, centroid, bounding box, site extents and the local UTM zone. This is issued as Deliverable D1a in Week 1, ahead of everything else, because it is the quantity against which the survey scope and the area-based fees in Section 10 are confirmed.'));
children.push(BUL('Procurement and quality review of all secondary data listed in Section 4.2, including record-length assessment, homogeneity and outlier screening of rainfall series, and identification of data gaps.'));
children.push(BUL('Reconnaissance survey of the entire boundary with a hydrologist and a highway engineer present together, covering drainage lines, tank bunds and surplus courses, existing culverts and causeways, existing village roads and their observed performance, gullied and eroded areas, and evidence of past inundation.'));
children.push(BUL('Structured historical-evidence capture: interviews with farmers, village elders, irrigation department field staff and local officials on flood paths, depths, dates, duration of access loss, tank overtopping and road washout history. Recorded, georeferenced and reported as a data set, not anecdote.'));
children.push(BUL('Review of any existing Client data (survey, geotechnical, EIA, feasibility) and reconciliation against the requirements of this study.'));
children.push(BULL('Deliverable D1 — Inception Report: ', 'confirmed methodology, agreed basis of design, adopted return periods and freeboards, data inventory and gap register, survey and investigation plan, and confirmed programme.'));

children.push(H2('6.2  Stage 2 — Topographic Survey and Terrain Model'));
children.push(P('This is the foundation of the study. Every flood level, drain gradient and culvert invert produced later is only as good as the terrain model, and on a low-relief undulating site with shallow ponding, vertical accuracy matters more than horizontal.'));
children.push(BULL('UAV survey of the entire boundary ', 'plus an agreed buffer beyond it, flown to produce a bare-earth Digital Terrain Model. Two technical options are offered in Section 10.2 (LiDAR, recommended; or photogrammetry).'));
children.push(BULL('Ground control and datum ', '— DGPS control network tied to Survey of India GTS benchmarks or CORS, with independent check points to verify and report achieved vertical accuracy against specification.'));
children.push(BULL('Terrain products ', '— bare-earth DTM at the agreed grid, contours at 0.5 m interval (0.25 m in flat zones), breaklines along all channels, bunds, roads and ridges, orthomosaic, and the full GIS geodatabase.'));
children.push(BULL('Detailed ground survey ', 'at every identified natural crossing and hydraulic feature: channel cross-sections upstream and downstream, long-sections along the channel, bed and bank levels, and existing high-flood-level marks where identifiable on the ground.'));
children.push(BULL('Inventory and condition survey ', 'of every existing hydraulic structure inside and immediately outside the boundary — culverts, causeways, tank sluices, surplus weirs, canals, field bunds, check dams — with dimensions, invert levels, condition, observed blockage and photographic record.'));
children.push(BULL('Deliverable D2 — Survey Report and Terrain Model: ', 'methodology, accuracy statement, control report, DTM, contours, orthomosaic, cross-sections, structure inventory, and GIS geodatabase.'));

children.push(H2('6.3  Stage 3 — Soil and Sub-surface Characterisation for Hydrology'));
children.push(P('Scoped to serve two purposes at once: to parameterise the hydrological model, and to provide the subgrade data needed for the road and drainage recommendations at Stage 8.'));
children.push(BUL('Investigation grid across the boundary at a density agreed at inception (indicatively one location per 100–150 ha), supplemented by a location at every identified crossing and at each candidate drainage corridor.'));
children.push(BUL('Trial pits to expose the soil profile, log horizon depths, record desiccation cracking, and establish the depth and lateral extent of the vertisol layer and the level of underlying weathered or hard strata.'));
children.push(BUL('Laboratory testing: grain-size distribution, Atterberg limits (liquid limit, plastic limit, plasticity index), free swell index, swelling pressure, shrinkage limit, OMC and MDD, and CBR in both soaked and unsoaked condition.'));
children.push(BUL('Field infiltration testing by double-ring infiltrometer at representative locations across each soil unit, and field permeability where required, to derive realistic infiltration parameters rather than textbook defaults.'));
children.push(BUL('Groundwater level observation, ideally in both pre-monsoon and post-monsoon condition, to identify areas where sub-surface drainage or raised formation will be required.'));
children.push(BULL('Deliverable D3 — Soil and Sub-surface Report, ', 'including a hydrological soil group map, a vertisol depth and extent map, a swell-potential zoning map, a soaked-CBR map, and the derived curve numbers and infiltration parameters for the hydrological model.'));

children.push(H2('6.4  Stage 4 — Catchment Delineation and Drainage Characterisation'));
children.push(BULL('Full catchment delineation ', 'from the terrain model, extended beyond the project boundary to include every external catchment that drains into the site. This is a specific and deliberate inclusion: a study confined to the boundary would systematically undersize every structure on the western and upslope margins.'));
children.push(BULL('Sub-catchment definition ', 'at each drainage node and prospective crossing, with stream ordering, drainage density, longest flow path, slope profile and time of concentration computed for each.'));
children.push(BULL('Irrigation tank cascade mapping ', '— identification of every minor-irrigation tank hydraulically connected to the site, whether upstream, within or downstream of the boundary; compilation of FTL, MWL and tank bund levels; mapping of feeder channels, surplus weirs and surplus courses; and identification of any encroachment of tank FTL or surplus course onto the project boundary.'));
children.push(BULL('Anthropogenic interference mapping ', '— existing road and rail embankments, canals, field bunds, quarries, borrow areas and check dams that already modify the natural drainage, together with their observed effect.'));
children.push(BULL('Deliverable D4 — Catchment Characterisation Report ', 'with the full catchment atlas and GIS layers.'));

children.push(H2('6.5  Stage 5 — Hydrological Analysis'));
children.push(H3('6.5.1  Design rainfall'));
children.push(BUL('Compilation of the annual maximum daily rainfall series for the site from IMD gridded and station data, with quality control, infilling of gaps by established methods, and testing for homogeneity, trend and outliers.'));
children.push(BUL('Frequency analysis by multiple candidate distributions — Gumbel (EV1), Generalised Extreme Value, Log-Pearson Type III and Log-Normal — fitted by the method of L-moments, with goodness-of-fit testing and selection of the best-fitting distribution on stated criteria. Regional frequency analysis will be applied where the local record length is insufficient to support a 100-year estimate directly.'));
children.push(BUL('Derivation of design rainfall depths for the 2, 5, 10, 25, 50, 100 and 200-year return periods, with confidence intervals reported so that the uncertainty in the long-return-period estimates is visible rather than implied.'));
children.push(BUL('Disaggregation to short durations (15 minutes to 24 hours) using IMD empirical reduction relationships and regional short-duration ratios, producing site-specific Intensity–Duration–Frequency curves and Depth–Duration–Frequency tables for the project.'));
children.push(BUL('Construction of design hyetographs for each return period and critical duration by the alternating-block method, with critical-duration testing at each catchment rather than a single assumed storm duration for the whole site.'));

children.push(H3('6.5.2  Climate change allowance for the 50–75 year horizon'));
children.push(P('This directly addresses the Client’s instruction to estimate for the next 50–75 years. Design rainfall derived from the historical record represents the climate that has been, not the climate the asset will meet.'));
children.push(BUL('Extraction of downscaled CMIP6 projections for the project grid cell under SSP2-4.5 and SSP5-8.5, for the 2050s and 2075s horizons, with bias correction against the observed record.'));
children.push(BUL('Derivation of projected change factors for short-duration rainfall extremes specifically, since projected changes in extreme intensity differ from — and generally exceed — projected changes in mean annual rainfall. In this region the projections point to a broadly stable or modestly changing annual total accompanied by intensification of extreme events, which is the combination most likely to defeat a design based on historical means.'));
children.push(BUL('Adoption of a design uplift factor on rainfall intensity, agreed with the Client at inception, and reporting of every design event both with and without the uplift so that the cost of resilience is explicit and the Client can make an informed commercial decision structure by structure.'));
children.push(BUL('Where an uplift would require a larger structure, we will state the incremental cost of building for it now against the cost and disruption of retrofitting later. On buried cross-drainage, building the larger size now is almost always the cheaper decision over 75 years, and we will say so where the numbers support it.'));

children.push(H3('6.5.3  Runoff estimation'));
children.push(BUL('SCS Curve Number method as the primary approach, with curve numbers derived from the measured hydrological soil groups and mapped land use from Stage 3, run at AMC-II and AMC-III conditions.'));
children.push(BUL('Rational method for small catchments (indicatively below 50 ha) serving side drains and minor culverts, with runoff coefficients justified from the measured soil and slope data.'));
children.push(BUL('Synthetic Unit Hydrograph per the applicable CWC Flood Estimation Report sub-zone, and regional flood formulae, applied as independent cross-checks. Where the methods diverge materially we will report the divergence and state the basis on which a value is adopted, rather than silently averaging.'));
children.push(BUL('Construction of a rainfall-runoff model (HEC-HMS or equivalent) covering the project catchments and all external contributing catchments, generating peak flows and full hydrographs at every drainage node and prospective crossing for each return period, with and without climate uplift.'));
children.push(BULL('Deliverable D5 — Hydrological Analysis Report, ', 'including the IDF curves, DDF tables, design hyetographs, climate-change assessment, and the design flow schedule at every node.'));

children.push(H2('6.6  Stage 6 — Two-Dimensional Hydraulic Modelling'));
children.push(P('A one-dimensional analysis of individual crossings would be inadequate on this site. The terrain is low-relief and undulating, flow paths are shallow, wide and diffuse, and roads and platforms will themselves redirect water. A two-dimensional model of the whole boundary is the only way to see what the development does to the drainage of the site as a system.'));
children.push(BULL('Model construction ', '— a 2D rain-on-grid model (HEC-RAS 2D or equivalent) built directly on the Stage 2 terrain model, covering the entire project boundary and buffer, with computational mesh refined along channels, drainage lines and prospective infrastructure corridors.'));
children.push(BULL('Parameterisation ', '— spatially distributed roughness from mapped land use, and spatially distributed infiltration from the Stage 3 soil groups. Inflows from external catchments applied at the model boundary as hydrographs from Stage 5.'));
children.push(BULL('Existing-condition simulation ', '— the site as it is today, for the 2, 5, 10, 25, 50, 100 and 200-year events, establishing the baseline drainage regime.'));
children.push(BULL('Developed-condition simulation ', '— the same events re-run with the proposed road network, platforms, drains and cross-drainage structures represented, to demonstrate the effect of the development and to verify that the proposed drainage design performs as intended.'));
children.push(P('Model outputs, produced for each return period and each condition:', { before: 120 }));
children.push(BUL('Maximum flood depth, maximum velocity, and depth×velocity hazard rating.', 1));
children.push(BUL('Flow direction and flow-path mapping, identifying the true flood conveyance corridors across the boundary.', 1));
children.push(BUL('Ponding depth and, critically, ponding duration — the length of time water stands at each location, which governs vertisol trafficability and subgrade saturation.', 1));
children.push(BUL('Overtopping locations along the proposed road network, with depth and duration of overtopping at each.', 1));
children.push(BUL('Afflux upstream of each proposed crossing, checked against the agreed limit and against third-party land.', 1));
children.push(P('Sensitivity and failure-mode runs:', { before: 120 }));
children.push(BUL('Climate-uplift scenario for the 2050s and 2075s horizons.', 1));
children.push(BUL('50% blockage of cross-drainage structures.', 1));
children.push(BUL('AMC-III antecedent wetness.', 1));
children.push(BUL('Surplus and spill routing from upstream irrigation tanks, including the routing of tank surplus through the project area.', 1));
children.push(BUL('Where any upstream tank’s failure envelope could reach project assets, a breach (dam-break) routing simulation for that tank, to establish whether the asset is exposed and what mitigation, if any, is warranted. Offered as an optional item in Section 10.3 since the number of such tanks is unknown until Stage 4.', 1));
children.push(BULL('Deliverable D6 — Hydraulic Modelling Report and Flood Hazard Atlas, ', 'a map set covering the whole boundary for every return period and scenario, with the model files handed over.'));

children.push(H2('6.7  Stage 7 — Erosion, Scour and Sediment Assessment'));
children.push(BUL('Soil-loss mapping across the boundary by RUSLE, using the measured soil data, the terrain model and mapped land use, identifying the areas most vulnerable to erosion during and after construction.'));
children.push(BUL('Sediment yield estimation at each drainage node, to size silt traps and sediment basins and to establish realistic desilting frequencies for the O&M manual.'));
children.push(BUL('Inventory of existing gullies and rills from imagery and ground survey, with assessment of active headward erosion — the most common cause of progressive damage to wind-farm access roads in this terrain.'));
children.push(BUL('Scour assessment at every proposed crossing: general and local scour by Lacey regime and IRC:5 / IRC:78 methods, checked against modelled velocities, with recommended foundation depths and protection works.'));
children.push(BUL('Bank stability assessment for the ephemeral sandy channels at crossing locations, and assessment of bed degradation or aggradation trends from the multi-date imagery.'));
children.push(BULL('Deliverable D7 — Erosion, Scour and Sediment Report ', 'with erosion risk mapping and the scour schedule.'));

/* ---- 6.8 DESIGN RECOMMENDATIONS ---- */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H2('6.8  Stage 8 — Design Recommendations and Drainage Master Plan'));
children.push(P('This stage is the substance of what the Client has asked for: advice on road design, drains and related works that can be taken to site and built. It is the largest stage in the study and the one against which the proposal should be judged.'));

children.push(H3('6.8.1  Boundary-wide hydrological constraint mapping'));
children.push(P('The Client has instructed that the 35 tentative WTG coordinates be disregarded and the entire boundary assessed. We therefore invert the conventional approach. Rather than testing a fixed layout, we classify the whole boundary and hand the Client a constraint surface that any layout can be tested against, now or in two years:'));
children.push(BULL('Zone A — Unsuitable: ', 'active floodway, high depth×velocity hazard, tank FTL and MWL extents, notified water-body land, and active gully systems. No permanent infrastructure to be sited here.'));
children.push(BULL('Zone B — Conditional: ', 'developable subject to defined mitigation. For every part of Zone B the report states the specific requirement — minimum platform level expressed as an absolute reduced level, required protection works, or required drainage provision — rather than a generic caution.'));
children.push(BULL('Zone C — Suitable: ', 'no significant hydrological constraint on siting.'));
children.push(P('This is issued as GIS layers together with a minimum-platform-level raster covering the entire boundary, so that when the layout evolves the Client can read the required formation level at any coordinate directly, without returning to us. One formal re-assessment of the final frozen layout against the constraint surface is included in the fee; further iterations are offered as an optional item.', { before: 100 }));

children.push(H3('6.8.2  Road network — alignment and vertical profile'));
children.push(BULL('Alignment principles, ', 'issued as mapped guidance over the constraint surface: favour ridge lines and interfluves; cross drainage lines square-on at the narrowest stable section; never align a road along a drainage line or a valley floor; maintain stated offsets from tank bunds, FTL and surplus courses; avoid crossing tank bunds entirely wherever an alternative exists, and where it does not, define the conditions under which it may be done.'));
children.push(BULL('Vertical profile criteria ', 'for each road class, with minimum formation level set as the greater of (i) design flood or ponding level plus freeboard and (ii) the minimum embankment height needed to keep the subgrade above the zone of seasonal moisture change in the vertisol. Low points in the profile are to be avoided or, where unavoidable, drained positively.'));
children.push(BULL('Cross-section and camber ', '— recommended camber of 2.5–3.0% to shed water quickly, shoulder width and treatment, side slopes, and turfing or protection of embankment slopes.'));
children.push(BULL('Road hierarchy ', '— a recommended classification into an all-weather spine, secondary WTG access spurs, and the village bypasses, each with its own design standard, return period and pavement recommendation. The bypasses are treated as public-interface roads and designed accordingly, including their interaction with village drainage.'));

children.push(H3('6.8.3  Black cotton soil — subgrade and moisture control'));
children.push(P('Specific, quantified recommendations, with the selection between options made on the measured swell and CBR data rather than by rule of thumb:'));
children.push(BULL('Subgrade treatment options, ', 'assessed and recommended zone by zone: excavation and replacement of the expansive layer to a depth set by the measured swell profile; lime stabilisation with the dosage fixed by pH and ICL testing; or lime–flyash stabilisation where economics favour it. The report states which applies where, with the reasoning.'));
children.push(BULL('Separation and reinforcement ', '— non-woven geotextile separator over the vertisol subgrade to prevent contamination of the granular layer, with biaxial geogrid reinforcement recommended in zones where soaked CBR falls below the stated threshold.'));
children.push(BULL('Blanket and capping course ', '— granular blanket thickness derived from the measured soaked CBR map, so that thickness varies with the ground rather than being applied uniformly across the site.'));
children.push(BULL('Moisture control — the decisive measure. ', 'Sealed and impervious shoulders, sealed cross-fall, intercepting and cut-off drains upslope of the formation, and sub-surface drainage where the groundwater observations require it. On expansive soil, keeping water out of the subgrade is more effective and far cheaper than designing the pavement to survive a saturated one.'));
children.push(BULL('Pavement recommendation by road class, ', 'with justification: an all-weather sealed or concrete spine road, against gravel or WBM construction on the spurs, evaluated on whole-life cost including the outage cost of lost access. Our expectation, to be confirmed by the analysis, is that a sealed spine built in the first dry season repays itself on this soil.'));

children.push(H3('6.8.4  Surface drainage system'));
children.push(BULL('Side drains ', '— lined trapezoidal or rectangular sections sized from the Stage 5 flows, with lining type, minimum longitudinal gradient and maximum permissible velocity stated for each reach. Unlined earthen drains are not recommended anywhere in vertisol; the report will say so explicitly and give the reason.'));
children.push(BULL('Mitre and turn-out drains ', 'at defined intervals so that side drains discharge frequently to natural ground rather than accumulating a large concentrated flow — the most common and most damaging drainage error on wind-farm road networks.'));
children.push(BULL('Catch-water and cut-off drains ', 'upslope of cuttings, embankments and platforms, sized for the intercepted catchment.'));
children.push(BULL('Perimeter drainage ', 'around every WTG hardstand, the substation, the O&M building and construction facilities, with defined outfall arrangements.'));
children.push(BULL('Outfalls and discharge control ', '— energy dissipation at every outfall, silt traps ahead of discharge, and a stated prohibition on discharging concentrated flow onto third-party agricultural land, which is a reliable source of dispute and compensation claims in this district.'));

children.push(H3('6.8.5  Cross-drainage structures'));
children.push(BULL('Structure-type selection matrix ', 'relating catchment area, design discharge, channel bed width and road class to the appropriate structure: pipe culvert (minimum 1200 mm diameter recommended for maintainability, whatever the hydraulic requirement), box culvert, slab culvert, vented causeway, submersible causeway with guide posts and depth markers for the wide sandy vankas, or minor bridge.'));
children.push(BULL('A sized schedule for every identified crossing ', 'on the network, tabulating: catchment area, design discharge, adopted return period, proposed structure type and vent size, invert and soffit levels, design headwater and afflux, outlet velocity, computed scour depth, required foundation depth, and the protection works required.'));
children.push(BULL('Protection works ', '— aprons and launching aprons, cut-off walls, gabion or riprap protection, guide bunds and flared wing walls, each sized to the computed scour and velocity rather than to a standard detail.'));
children.push(BULL('Causeway policy ', '— where a submersible crossing is the correct engineering and economic answer on a wide ephemeral channel, we will recommend it, together with the operational protocol that must accompany it: depth markers, guide posts, a defined no-crossing depth, and the implications for emergency access and for major-component logistics.'));

children.push(H3('6.8.6  Cable trench and balance-of-plant drainage'));
children.push(BULL('Cable trenches act as preferential drainage paths ', 'and are a frequently overlooked failure mechanism: a trench backfilled with granular material through low-permeability vertisol becomes a French drain, conveying water along the alignment and discharging it where it is not wanted — often into a road formation or a foundation.'));
children.push(BUL('Recommendations will cover clay or bentonite cut-off plugs at defined spacing, controlled relief and discharge points, backfill and compaction specification, and restrictions on trench alignment along contours on sloping ground.'));
children.push(BUL('Drainage provisions for the substation and pooling station platform, the O&M building, laydown yards, batching plant and construction camps.'));

children.push(H3('6.8.7  Erosion and sediment control'));
children.push(BUL('Permanent measures: turfing and vegetative protection of slopes, coir or jute geotextiles on erodible faces, check dams and gully plugs in the ephemeral channels, and stabilisation of identified active gully heads.'));
children.push(BUL('Construction-phase measures: silt fences, sediment basins, staged clearing to limit exposed area, temporary diversion arrangements, and stabilisation of disturbed ground before each monsoon.'));
children.push(BUL('A construction-phase erosion and sediment control plan that can be issued to the EPC contractor as a specification, with hold points.'));

children.push(H3('6.8.8  Water balance, harvesting and recharge'));
children.push(BUL('Assessment of construction-phase water demand against local availability — a material issue in a chronically drought-affected district where competition with agricultural and domestic use carries reputational and permitting consequences.'));
children.push(BUL('Identification of opportunities for percolation ponds, recharge structures and farm ponds using the natural depressions and flow paths identified by the model, sited so that they do not create new ponding against roads or platforms.'));
children.push(BUL('This is offered both as good practice and as a defensible community and regulatory position: the project can demonstrably improve local water security rather than merely avoid harming it.'));

children.push(H3('6.8.9  Trafficability and construction workability calendar'));
children.push(P('A direct response to the Client’s stated experience that the site cannot be entered until it dries. We will convert that observation into a planning tool:'));
children.push(BUL('Analysis of the long-period daily rainfall record to establish the frequency and seasonal distribution of rainfall events by depth class.'));
children.push(BUL('Estimation of drying time following an event, by soil zone and event depth, from the measured soil properties and evaporation data.'));
children.push(BUL('A month-by-month expected workable-days calendar for the site, with confidence bands, distinguishing untreated ground from ground served by the all-weather spine.'));
children.push(BUL('Construction sequencing advice derived from it, including the case for constructing the spine road and the primary cross-drainage in the first available dry window, before bulk civil and erection activity begins. On this soil the sequencing decision is usually worth more to the programme than any other single recommendation in the report.'));
children.push(BULL('Deliverable D8 — Drainage Master Plan and Design Recommendations Report, ', 'with the structure schedule, typical design drawings, indicative BOQ and quantities, and the full GIS layer set.'));

children.push(H2('6.9  Stage 9 — Lifetime Resilience, O&M and Handover'));
children.push(BULL('Residual risk register ', 'covering the full 75-year horizon, by asset class, stating for each residual risk the exposure, the likelihood, the consequence and the recommended treatment or acceptance.'));
children.push(BULL('Operation and maintenance manual ', '— inspection protocol and frequency, pre-monsoon and post-monsoon actions, desilting frequencies derived from the computed sediment yields, culvert clearing before the North-East monsoon specifically, and defined trigger levels for intervention.'));
children.push(BULL('Monitoring recommendations ', '— siting of automatic rain gauges and staff gauges at key crossings, the data to be recorded, and the review cycle, so that the design assumptions can be verified against reality as the asset ages.'));
children.push(BULL('Recommendation for periodic re-assessment ', 'at a defined interval (we suggest five-yearly, and after any event exceeding a stated threshold), which over a 75-year life is the only credible way to keep a design current against a changing climate.'));
children.push(BULL('Reporting and workshops ', '— a design workshop with the Client and the EPC contractor on the draft findings, and a final presentation to Client management.'));
children.push(BULL('Deliverables D9–D11 ', '— Climate Resilience and Residual Risk Note, O&M Manual, and Final Consolidated Report with presentation.'));

/* ---- 7. EXCLUSIONS ---- */
children.push(H1('7.  Scope Boundaries and Exclusions'));
children.push(P('Stated plainly so that there is no ambiguity at invoicing. Any of the following can be added by agreement.'));
children.push(BUL('Detailed structural design and GFC drawings for cross-drainage structures. This proposal delivers hydraulic sizing, levels, foundation depths and typical drawings; structural detailing is offered as an optional item (Section 10.3).'));
children.push(BUL('Geotechnical investigation for WTG foundation design. The Stage 3 investigation is scoped for hydrological and subgrade purposes and is not a substitute for foundation-level investigation.'));
children.push(BUL('Pavement structural design to IRC:37 for the final network. Recommendations, subgrade parameters and a design basis are provided; formal pavement design is optional.'));
children.push(BUL('Statutory approvals, NOCs and liaison with regulatory bodies. We will provide the technical inputs and supporting documentation; the applications remain with the Client.'));
children.push(BUL('Environmental impact assessment, ecological survey, and social impact or resettlement studies.'));
children.push(BUL('Construction supervision, quality control and site inspection during execution, other than the optional visits in Section 10.3.'));
children.push(BUL('Land acquisition support, cadastral or boundary demarcation survey, and title verification.'));
children.push(BUL('Any tender or contract documentation for the civil works.'));

/* ---- 8. DELIVERABLES ---- */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1('8.  Deliverables'));
children.push(P('All reports are issued first as a draft for Client review and then as a final incorporating the Client’s comments. Weeks shown are from the effective start date defined in Section 9.'));

children.push(makeTable([620, 3080, 3646, 1200, 1200], ['Ref', 'Deliverable', 'Contents', 'Format', 'Week'], [
  ['D1', 'Inception Report', 'Confirmed methodology, agreed basis of design, return periods, data inventory and gap register, survey plan, programme', 'PDF + Word', '3'],
  ['D1a', 'Verified Boundary KML and Area Statement', 'Validated boundary geometry; Google Earth KML (styled, labelled, area embedded); area schedule in sq km / ha / acres; perimeter, centroid, bounding box, extents, UTM zone', 'KML + Excel + PDF', '1'],
  ['D2', 'Survey Report and Terrain Model', 'Accuracy statement, control report, DTM, 0.5 m contours, orthomosaic, cross-sections, existing structure inventory', 'PDF + GIS + CAD', '8'],
  ['D3', 'Soil and Sub-surface Report', 'Test results, hydrological soil group map, vertisol extent and depth, swell zoning, soaked-CBR map, model parameters', 'PDF + GIS', '10'],
  ['D4', 'Catchment Characterisation Report', 'Catchment and sub-catchment atlas, stream network, tank cascade and FTL/MWL mapping, interference mapping', 'PDF + GIS', '12'],
  ['D5', 'Hydrological Analysis Report', 'Frequency analysis, IDF curves and DDF tables, design hyetographs, climate-change assessment, design flow schedule at every node', 'PDF + Excel', '15'],
  ['D6', 'Hydraulic Modelling Report and Flood Hazard Atlas', 'Model report, depth / velocity / hazard / ponding-duration maps for all return periods and scenarios, overtopping schedule, model files', 'PDF + GIS + model', '19'],
  ['D7', 'Erosion, Scour and Sediment Report', 'RUSLE soil-loss mapping, sediment yield, gully inventory, scour schedule at all crossings', 'PDF + GIS', '20'],
  ['D8', 'Drainage Master Plan and Design Recommendations', 'Constraint zoning and minimum-platform-level raster, road alignment and profile guidance, BC-soil treatments, drainage design, sized structure schedule, typical drawings, indicative BOQ', 'PDF + CAD + GIS + Excel', '23'],
  ['D9', 'Climate Resilience and Residual Risk Note', '50 and 75-year assessment, uplift factors adopted, residual risk register by asset class, adaptation recommendations', 'PDF', '24'],
  ['D10', 'O&M Manual', 'Inspection and maintenance regime, desilting frequencies, trigger levels, monitoring plan, seasonal action checklist', 'PDF + Word', '24'],
  ['D11', 'Final Consolidated Report and Presentation', 'Integrated final report, executive summary, design workshop and final presentation to management', 'PDF + PPT', '26'],
  ['D12', 'GIS Geodatabase and Model Handover', 'Complete geodatabase, all model files, calculation sheets and raw survey data, with a handover note', 'Native formats', '26'],
], { centerCols: [0, 4] }));

children.push(P('Two hard copies of each final report will be issued in addition to electronic copies, unless a different number is requested. All GIS and model files are handed over in native, editable format — we do not issue locked or output-only deliverables.', { before: 140 }));

/* ---- 9. PROGRAMME ---- */
children.push(H1('9.  Programme'));
children.push(P('Twenty-six weeks from the effective start date, which is the later of the date of the work order and the date of receipt of the Client inputs marked essential in Section 4.1, together with site access.'));

children.push(makeTable([2900, 1100, 5746], ['Stage', 'Weeks', 'Notes'], [
  ['1 — Inception and data review', '1–3', 'Includes reconnaissance and historical evidence capture'],
  ['2 — Topographic survey', '3–8', 'Field stage. Weather-dependent; requires a dry window and land access'],
  ['3 — Soil investigation', '4–10', 'Field and laboratory stage; runs partly in parallel with Stage 2'],
  ['4 — Catchment characterisation', '9–12', 'Requires the terrain model from Stage 2'],
  ['5 — Hydrological analysis', '11–15', 'Partly parallel with Stage 4'],
  ['6 — Hydraulic modelling', '15–19', 'The longest desk stage; scenario runs are computationally heavy'],
  ['7 — Erosion, scour and sediment', '18–20', 'Parallel with the later part of Stage 6'],
  ['8 — Design recommendations and master plan', '19–23', 'Includes the design workshop with the Client and EPC contractor'],
  ['9 — Resilience, O&M and final reporting', '23–26', 'Includes final presentation and handover'],
], { centerCols: [1] }));

children.push(NOTE('Programme risks, stated up front', [
  'Weather. Stages 2 and 3 cannot be executed on wetted vertisol. An unseasonal wet spell will extend the field programme, and we will not compromise data quality to hold a date.',
  'Land access. Delay in landowner permission for survey and trial pits on private agricultural land is the most common cause of slippage on projects of this type. Client support under item 11 of Section 4.1 materially reduces this risk.',
  'Client review turnaround. The programme assumes ten working days for Client comment on each draft deliverable. Longer review periods extend the programme day for day.',
  'Late receipt of the road network concept. If the concept network is not available by Week 12, we will develop an indicative network to allow Stage 6 to proceed, and re-run the developed-condition assessment against the Client network when it is issued.',
]));

/* ---- 10. COMMERCIALS ---- */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1('10.  Commercial Proposal'));

children.push(NOTE('Basis of the quantities', [
  'The boundary area has been assumed at 80 sq km pending receipt of the georeferenced boundary. Unit rates are firm and will not change. Area-based line items (Parts B and D) will be restated against the actual notified area on receipt of the KML/shapefile, and a revised total issued before contract. The governing area will be the net enclosed area established in Deliverable D1a, computed on the WGS84 ellipsoid, so that both parties work to the same audited number rather than to a figure scaled off a drawing.',
  'All figures are in Indian Rupees and are exclusive of GST.',
]));

children.push(H2('10.1  Option 1 — Full study with UAV LiDAR survey (recommended)'));
children.push(makeTable([820, 4000, 1300, 1500, 2126], ['Part', 'Description', 'Unit', 'Qty / Rate', 'Amount (₹)'], [
  ['A', 'Mobilisation, secondary data acquisition, reconnaissance, historical evidence survey, desk review and Inception Report (D1)', 'Lump sum', '—', '6,50,000'],
  ['B', 'UAV LiDAR topographic survey, ground control, bare-earth DTM, 0.5 m contours, orthomosaic and geodatabase (D2)', 'per sq km', '80 @ 48,000', '38,40,000'],
  ['C', 'Detailed ground survey at crossings and hydraulic features; inventory and condition survey of existing structures', 'Lump sum', '—', '4,50,000'],
  ['D', 'Soil and sub-surface investigation for hydrology: trial pits, laboratory testing, infiltration and groundwater observation (D3)', 'per location', '60 @ 18,000', '10,80,000'],
  ['E', 'Catchment characterisation, tank cascade mapping and drainage network analysis (D4)', 'Lump sum', '—', '5,50,000'],
  ['F', 'Hydrological analysis: frequency analysis, IDF/DDF derivation, climate-change assessment, rainfall-runoff modelling (D5)', 'Lump sum', '—', '7,50,000'],
  ['G', '2D hydraulic modelling of the full boundary, all return periods and sensitivity scenarios, flood hazard atlas (D6)', 'Lump sum', '—', '12,50,000'],
  ['H', 'Erosion, scour and sediment assessment (D7)', 'Lump sum', '—', '4,00,000'],
  ['I', 'Drainage Master Plan and design recommendations: constraint mapping, road and drainage design advice, structure schedule, typical drawings, indicative BOQ (D8)', 'Lump sum', '—', '14,50,000'],
  ['J', 'Lifetime resilience and residual risk, O&M manual, final consolidated reporting, workshops and handover (D9–D12)', 'Lump sum', '—', '4,50,000'],
  { cells: ['', 'Total — Option 1 (exclusive of GST)', '', '', '1,08,70,000'], __bold: true, __fill: 'D9E2F3' },
], { centerCols: [0, 2, 3], rightCols: [4] }));
children.push(P('Rupees one crore eight lakh seventy thousand only, exclusive of GST.', { italics: true, color: GREY, size: 19 }));

children.push(H2('10.2  Option 2 — Full study with UAV photogrammetric survey'));
children.push(P('Identical in every respect except Part B. Photogrammetry derives the terrain surface from imagery rather than laser returns. On this site the vegetation is predominantly low scrub and seasonal agriculture, so a usable bare-earth model is achievable, but ground penetration under thorn scrub and tree cover is poorer and the achievable vertical accuracy is lower.'));
children.push(makeTable([820, 4000, 1300, 1500, 2126], ['Part', 'Description', 'Unit', 'Qty / Rate', 'Amount (₹)'], [
  ['B', 'UAV photogrammetric survey, ground control, DTM, contours, orthomosaic and geodatabase (D2)', 'per sq km', '80 @ 22,000', '17,60,000'],
  ['—', 'All other parts (A, C to J) as Option 1', '—', '—', '70,30,000'],
  { cells: ['', 'Total — Option 2 (exclusive of GST)', '', '', '87,90,000'], __bold: true, __fill: 'D9E2F3' },
], { centerCols: [0, 2, 3], rightCols: [4] }));
children.push(P('Rupees eighty-seven lakh ninety thousand only, exclusive of GST.', { italics: true, color: GREY, size: 19 }));

children.push(NOTE('Our recommendation between the two options', [
  'We recommend Option 1. On a low-relief site where ponding depths of 200–300 mm determine whether a road remains trafficable, the vertical accuracy of the terrain model is the accuracy of the whole study, and every flood level, drain gradient and culvert invert inherits it. The difference of approximately ₹ 21 lakh is around 20% of the fee but a much smaller fraction of the civil works it governs, and an under-resolved terrain model cannot be corrected later without reflying the site.',
  'Option 2 is a legitimate choice if budget is the binding constraint. If it is selected we will state the achieved accuracy explicitly and flag any conclusion that is sensitive to it, rather than presenting the results at a confidence the data does not support.',
]));

children.push(H2('10.3  Optional items — quoted for information, not included above'));
children.push(makeTable([620, 5000, 1900, 2226], ['#', 'Item', 'Unit', 'Rate (₹)'], [
  ['O1', 'Tank breach (dam-break) analysis and consequence assessment, per upstream tank identified as posing exposure to project assets', 'per tank', '1,25,000'],
  ['O2', 'Re-assessment of a revised WTG layout against the constraint surface, beyond the one iteration included in the fee', 'per iteration', '2,50,000'],
  ['O3', 'Detailed structural design and GFC drawings for cross-drainage structures', 'per structure', '35,000'],
  ['O4', 'Formal pavement design to IRC:37 for the finalised road network', 'Lump sum', '6,50,000'],
  ['O5', 'Construction-phase technical support and site visits (3 days per visit, inclusive of travel)', 'per visit', '85,000'],
  ['O6', 'Post-monsoon performance review in the first operating year, with recommendations', 'Lump sum', '3,50,000'],
  ['O7', 'Additional soil investigation locations beyond the 60 allowed', 'per location', '18,000'],
  ['O8', 'Additional survey area beyond the notified boundary, if required', 'per sq km', 'at Part B rate'],
], { centerCols: [0, 2], rightCols: [3] }));

children.push(H2('10.4  Payment schedule'));
children.push(makeTable([1200, 6346, 2200], ['Milestone', 'Trigger', 'Proportion'], [
  ['1', 'On award of work order and signature of agreement (advance)', '15%'],
  ['2', 'On acceptance of the Inception Report (D1)', '10%'],
  ['3', 'On completion of field survey and investigation, and acceptance of D2 and D3', '25%'],
  ['4', 'On acceptance of the Hydrological Analysis Report (D5)', '15%'],
  ['5', 'On acceptance of the Hydraulic Modelling Report and Flood Hazard Atlas (D6)', '15%'],
  ['6', 'On submission of the draft Drainage Master Plan (D8)', '10%'],
  ['7', 'On acceptance of the Final Consolidated Report and handover (D11, D12)', '10%'],
  { cells: ['', 'Total', '100%'], __bold: true, __fill: 'D9E2F3' },
], { centerCols: [0], rightCols: [2] }));

children.push(H2('10.5  Commercial terms'));
children.push(BUL('Prices are exclusive of GST, which will be charged at the rate prevailing at the date of invoice. TDS as applicable.'));
children.push(BUL('Payment within 30 days of invoice.'));
children.push(BUL('Rates are firm for the duration of the programme, subject to the effective start date falling within the validity period of this proposal.'));
children.push(BUL('All travel, accommodation, survey equipment, laboratory charges and reproduction costs for the scope described are included. No reimbursables are claimed against Parts A to J.'));
children.push(BUL('Statutory fees, third-party data purchase charges and government levies, if any, are at actuals against documentation.'));
children.push(BUL('UAV operations will be conducted in compliance with prevailing DGCA regulations; obtaining flight permissions is included in our scope, and Client support with local administration is assumed.'));
children.push(BUL('Intellectual property in the deliverables passes to the Client on receipt of final payment. We retain the right to use the methodology and anonymised learning.'));
children.push(BUL('Professional indemnity and liability as per the agreement to be executed; our standard terms will be furnished on request.'));
children.push(BUL('This proposal is valid for 60 days from the date of issue.'));

/* ---- 11. CLOSING ---- */
children.push(H1('11.  Points We Would Draw to the Client’s Attention'));
children.push(P('Four matters are worth raising now rather than at the report stage, because each affects a decision the Client is likely to take before this study concludes.'));

children.push(BULL('1.  The constraint surface is more valuable to you than a layout assessment. ', 'Because the WTG coordinates will change, the durable output of this study is the boundary-wide minimum-platform-level surface and constraint zoning. It remains valid as the layout evolves and can be handed straight to the micrositing and EPC teams. We have deliberately structured Stage 8 around it.'));

children.push(BULL('2.  Sequencing may matter more than any single design recommendation. ', 'On black cotton soil, building the all-weather spine road and its cross-drainage in the first dry window — before bulk civil works and erection — usually protects the programme more than any incremental structure sizing. If the construction programme is being fixed now, we would ask to be consulted on this point before the study concludes, and we are content to give an early view at no additional cost.'));

children.push(BULL('3.  The irrigation tanks deserve early attention. ', 'Tank FTL encroachment and obstruction of surplus courses are the most common cause of dispute, stop-work notice and forced redesign on wind projects in Rayalaseema. Stage 4 addresses it, but if any land parcels are being finalised before Week 12 we would recommend a preliminary tank-cascade screening ahead of the main programme. We will do this within Part A if asked.'));

children.push(BULL('4.  The two missing attachments should be reconciled before contract. ', 'Please issue the Scope of Work / Methodology / Reports document and the georeferenced boundary, in any format you hold it — KML, KMZ, shapefile, GeoJSON, or simply a list of corner coordinates. We will return the verified boundary KML and area statement (D1a) within one week of receipt, reconcile this proposal against the Client’s own scope document, confirm the area-based quantities, and reissue as R1 for signature. We do not anticipate a change in unit rates.'));

children.push(SPACER(300));
children.push(P('We would be glad to discuss any part of this proposal, and can attend a technical meeting or a site visit at short notice.', { before: 200 }));

children.push(SPACER(500));
children.push(makeTable([4873, 4873], null, [
  [[['For and on behalf of', { bold: false }]], [['Accepted for and on behalf of', { bold: false }]]],
  [' ', ' '],
  [' ', ' '],
  [' ', ' '],
  ['Name:  ______________________', 'Name:  ______________________'],
  ['Designation:  ________________', 'Designation:  ________________'],
  ['Date:  ______________________', 'Date:  ______________________'],
]));

/* ---- static table of contents (page numbers resolved by the 2-pass build) ---- */
const tocParas = tocEntries
  .filter((e) => e.text !== 'Contents')
  .map((e) => new Paragraph({
    spacing: { after: e.lvl === 1 ? 60 : 30, before: e.lvl === 1 ? 90 : 0 },
    indent: { left: e.lvl === 1 ? 0 : 340 },
    tabStops: [{ type: TabStopType.RIGHT, position: TW - 40, leader: LeaderType.DOT }],
    children: [
      new TextRun({ text: e.text, bold: e.lvl === 1, size: e.lvl === 1 ? 20 : 19,
                    color: e.lvl === 1 ? NAVY : '404040', font: 'Calibri' }),
      new TextRun({ children: [new Tab()] }),
      new TextRun({ text: String(PAGEMAP[tocNorm(e.text)] === undefined ? '' : PAGEMAP[tocNorm(e.text)]),
                    bold: e.lvl === 1, size: e.lvl === 1 ? 20 : 19,
                    color: e.lvl === 1 ? NAVY : '404040', font: 'Calibri' }),
    ],
  }));
children.splice(TOC_AT, 0, ...tocParas);

/* ================= ASSEMBLE ================= */
const doc = new Document({
  creator: '',
  title: 'Techno-Commercial Proposal — Hydrology Study, Wind Project, Anantapur',
  description: 'Hydrology, hydraulics and drainage design study proposal',
  numbering: {
    config: [{
      reference: 'bullets',
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 360, hanging: 220 } } } },
        { level: 1, format: LevelFormat.BULLET, text: '◦', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 220 } } } },
      ],
    }],
  },
  styles: {
    default: {
      document: { run: { font: 'Calibri', size: 20 } },
    },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Calibri', size: 28, bold: true, color: NAVY } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Calibri', size: 23, bold: true, color: ACCENT } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Calibri', size: 21, bold: true, color: '333333' } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1100, right: MARGIN, bottom: 1100, left: MARGIN, header: 560, footer: 560 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF', space: 4 } },
          children: [new TextRun({ text: 'Techno-Commercial Proposal  —  Hydrology Study, Wind Project, Anantapur District, AP', size: 16, color: GREY, font: 'Calibri' })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF', space: 4 } },
          children: [
            new TextRun({ text: 'Rev R0   |   Page ', size: 16, color: GREY, font: 'Calibri' }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY, font: 'Calibri' }),
            new TextRun({ text: ' of ', size: 16, color: GREY, font: 'Calibri' }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: GREY, font: 'Calibri' }),
          ],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2] || 'proposal.docx', buf);
  console.log('written:', (buf.length / 1024).toFixed(1), 'KB');
});
